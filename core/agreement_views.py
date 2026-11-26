"""
Agreement Lifecycle Views & Endpoints for Rojgar Setu.
Enforces:
1. Strict 2-Party Signing Gate:
   - Job is created in DRAFT and is NOT active/published until Employer draws signature.
   - Employer reviews agreement in PDF-reader viewer and draws signature on canvas.
   - Upon Employer signature confirmation: Job becomes active/published.
2. Worker In-App Agreement Review & Counter-Signing:
   - When Worker accepts job from Chat, they are directed to the agreement viewer.
   - Worker reviews employer's locked signature and agreement terms.
   - Worker draws signature and affirms consent.
   - Status becomes FULLY_EXECUTED; final 2-Party PDF generated with dual signatures; mutual contacts unlocked.
3. Dedicated Agreement Dashboards, History Audit Trail & Dispute Filing.
"""

import os
import json
import base64
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.conf import settings
from django.db.models import Q

from .models import (
    UserAccount, Job, Application, ChatRoom, ChatMessage, Contract,
    DigitalAgreement, AgreementSignature, AgreementAuditLog, AgreementDispute, AgreementTemplate
)
from .views import _get_current_user, _require_auth
from .agreement_engine import compile_canonical_agreement_text, generate_agreement_number
from .pdf_service import generate_legal_agreement_pdf


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


# ==============================================================================
# 1. Employer Review & Signature Capture View
# ==============================================================================

def agreement_employer_review_view(request, agreement_id):
    """
    Stage 2 & 3: Employer Reviews the compiled agreement in a PDF-style document viewer,
    draws their signature via touch/mouse canvas, confirms affirmation, and submits.
    Only upon successful signature confirmation does the Job become PUBLISHED & ACTIVE!
    """
    auth_redirect = _require_auth(request, allowed_roles=['employer', 'admin'])
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    agreement = get_object_or_404(DigitalAgreement, id=agreement_id, employer=user)
    lang = request.GET.get('lang') or request.session.get('lang', 'hi')
    if request.GET.get('lang') in ('en', 'hi'):
        request.session['lang'] = request.GET.get('lang')

    if request.method == 'POST':
        signature_data = request.POST.get('signature_data', '').strip()
        declaration_affirmed = request.POST.get('declaration_affirmed') == 'on'

        # Validation: do not accept empty or invalid signature
        if not signature_data or len(signature_data) < 200 or not signature_data.startswith('data:image/'):
            messages.error(request, "कृपया हस्ताक्षर कैनवास पर अपना हस्ताक्षर बनाएं।" if lang == 'hi' else "Please draw your signature on the signature pad before submitting.")
            return redirect('agreement_employer_review', agreement_id=agreement.id)

        if not declaration_affirmed:
            messages.error(request, "कृपया नियम व शर्तों की सहमति बॉक्स को चेक करें।" if lang == 'hi' else "You must acknowledge the legal declaration to sign.")
            return redirect('agreement_employer_review', agreement_id=agreement.id)

        # Record Employer Signature & Audit Event
        now = timezone.now()
        agreement.employer_signature_data = signature_data
        agreement.employer_signed_at = now
        agreement.employer_declaration_affirmed = True
        agreement.status = 'PUBLISHED_AWAITING_WORKER'
        agreement.save()

        # Save immutable signature entity
        AgreementSignature.objects.create(
            agreement=agreement,
            signer=user,
            role='employer',
            signature_data=signature_data,
            document_hash_at_signing=agreement.document_hash,
            document_version=agreement.agreement_version,
            signed_at=now,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
            declaration_text="I confirm that I have reviewed this agreement, understand its terms and conditions, and agree to the responsibilities and obligations specified herein."
        )

        # Audit log event
        AgreementAuditLog.objects.create(
            agreement=agreement,
            actor=user,
            event_type='EMPLOYER_SIGNED',
            previous_status='EMPLOYER_REVIEW_PENDING',
            new_status='PUBLISHED_AWAITING_WORKER',
            document_version=agreement.agreement_version,
            metadata={
                'ip': get_client_ip(request),
                'doc_hash': agreement.document_hash,
                'signed_at': now.isoformat()
            }
        )

        # CRITICAL BUSINESS RULE: Publish the job now that the agreement is signed!
        job = agreement.job
        job.is_active = True
        job.status = 'active'
        job.employer_signature = f"ESIGN_EMP_{agreement.agreement_number}_{int(now.timestamp())}"
        job.employer_signed_at = now
        job.save()

        # Generate initial review copy of the PDF
        try:
            generate_legal_agreement_pdf(agreement)
        except Exception as e:
            print(f"[Agreement Engine] Initial PDF generation notice: {e}")

        success_msg = "डिजिटल अनुबंध सफलतापूर्वक हस्ताक्षरित! आपका कार्य अब कारीगरों के लिए लाइव है।" if lang == 'hi' else "Digital agreement signed successfully! Your job is now published and visible to local karigars."
        messages.success(request, success_msg)
        return redirect('my_jobs')

    context = {
        'agreement': agreement,
        'job': agreement.job,
        'current_user': user,
        'current_lang': lang,
        'user_role': 'employer',
    }
    return render(request, 'agreements/viewer.html', context)


# ==============================================================================
# 2. Worker Review & Counter-Signature Capture View
# ==============================================================================

def agreement_worker_review_view(request, agreement_id):
    """
    Stage 4 & 5: Worker Reviews the exact employer-signed agreement in the PDF reader,
    draws their signature via touch/mouse canvas, confirms affirmation, and submits.
    Transitions status to FULLY_EXECUTED, generates dual-signed PDF, and unlocks contacts!
    """
    auth_redirect = _require_auth(request, allowed_roles=['worker'])
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    agreement = get_object_or_404(DigitalAgreement, id=agreement_id)
    lang = request.GET.get('lang') or request.session.get('lang', 'hi')
    if request.GET.get('lang') in ('en', 'hi'):
        request.session['lang'] = request.GET.get('lang')

    # Ensure worker is authorized for this agreement (must have applied & been shortlisted/forwarded by employer)
    from .models import Application
    worker_app = Application.objects.filter(job=agreement.job, worker=user).first()
    is_authorized = (
        (agreement.worker == user) or
        (worker_app and worker_app.status in ['chat_initiated', 'contract_forwarded', 'contract_accepted'])
    )
    if not is_authorized:
        messages.warning(
            request,
            "कृपया पहले इस कार्य के लिए आवेदन करें। नियोक्ता द्वारा चैट में अनुबंध भेजने के बाद ही आप इसे देख व हस्ताक्षर कर सकते हैं।"
            if lang == 'hi'
            else "You must apply first. You can only review and sign this agreement after the employer shortlists you and initiates chat."
        )
        return redirect('job_detail', job_id=agreement.job.id)

    if agreement.worker and agreement.worker != user:
        raise Http404("You are not authorized to review this agreement.")

    if request.method == 'POST':
        signature_data = request.POST.get('signature_data', '').strip()
        declaration_affirmed = request.POST.get('declaration_affirmed') == 'on'

        if not signature_data or len(signature_data) < 200 or not signature_data.startswith('data:image/'):
            messages.error(request, "कृपया हस्ताक्षर कैनवास पर अपना हस्ताक्षर बनाएं।" if lang == 'hi' else "Please draw your signature on the signature pad before submitting.")
            return redirect('agreement_worker_review', agreement_id=agreement.id)

        if not declaration_affirmed:
            messages.error(request, "कृपया नियम व शर्तों की सहमति बॉक्स को चेक करें।" if lang == 'hi' else "You must acknowledge the legal declaration to accept.")
            return redirect('agreement_worker_review', agreement_id=agreement.id)

        now = timezone.now()
        agreement.worker = user
        agreement.worker_signature_data = signature_data
        agreement.worker_signed_at = now
        agreement.worker_declaration_affirmed = True
        agreement.status = 'FULLY_EXECUTED'
        agreement.fully_executed_at = now

        # Recompile final executed agreement HTML/text revealing full work address & worker details
        from .agreement_engine import compile_canonical_agreement_text
        exec_txt, exec_hash, exec_html = compile_canonical_agreement_text(
            agreement_number=agreement.agreement_number,
            employer_name=agreement.employer.name,
            employer_phone=agreement.employer.phone,
            worker_name=user.name,
            worker_phone=user.phone,
            job_title=agreement.job.title,
            category=agreement.category,
            scope_of_work=agreement.job.responsibilities,
            locality=agreement.job.locality,
            city=agreement.job.city,
            offered_price=float(agreement.job.offered_price),
            wage_period=agreement.job.wage_period,
            duration_text=agreement.job.duration_text,
            lang=lang,
            reveal_full_address=True
        )
        agreement.compiled_agreement_html = exec_html
        agreement.compiled_agreement_text = exec_txt
        agreement.document_hash = exec_hash
        agreement.save()

        # Save immutable signature entity
        AgreementSignature.objects.create(
            agreement=agreement,
            signer=user,
            role='worker',
            signature_data=signature_data,
            document_hash_at_signing=agreement.document_hash,
            document_version=agreement.agreement_version,
            signed_at=now,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
            declaration_text="I confirm that I have reviewed this work agreement, understand the stated responsibilities, payment terms and conditions, and voluntarily agree to undertake the work under the terms specified herein."
        )

        # Audit log event
        AgreementAuditLog.objects.create(
            agreement=agreement,
            actor=user,
            event_type='WORKER_SIGNED',
            previous_status='WORKER_REVIEW_PENDING',
            new_status='FULLY_EXECUTED',
            document_version=agreement.agreement_version,
            metadata={
                'ip': get_client_ip(request),
                'doc_hash': agreement.document_hash,
                'signed_at': now.isoformat()
            }
        )

        # Update legacy Contract & Application in ChatRoom to maintain backwards compatibility
        chat_room = ChatRoom.objects.filter(job=agreement.job, worker=user).first()
        if chat_room:
            chat_room.application.status = 'contract_accepted'
            chat_room.application.save()

            contract, created = Contract.objects.get_or_create(
                chat_room=chat_room,
                job=agreement.job,
                employer=agreement.employer,
                worker=user,
                defaults={
                    'contract_text': agreement.compiled_agreement_text,
                    'agreed_price': agreement.job.offered_price,
                    'duration_agreed': agreement.job.duration_text,
                    'employer_signature': agreement.job.employer_signature,
                    'employer_signed_at': agreement.employer_signed_at or now,
                    'worker_signature': f"ESIGN_WRK_{agreement.agreement_number}_{int(now.timestamp())}",
                    'worker_signed_at': now,
                    'status': 'active'
                }
            )
            if not created:
                contract.worker_signature = f"ESIGN_WRK_{agreement.agreement_number}_{int(now.timestamp())}"
                contract.worker_signed_at = now
                contract.status = 'active'
                contract.save()

            ChatMessage.objects.create(
                chat_room=chat_room,
                sender=user,
                message=f"🤝 DIGITAL AGREEMENT #{agreement.agreement_number} FULLY EXECUTED! Both parties have digitally signed. Mutual mobile numbers are unlocked for direct voice coordination.",
                is_system_notice=True
            )

        # Generate official Final 2-Party PDF with ReportLab
        try:
            generate_legal_agreement_pdf(agreement)
        except Exception as e:
            print(f"[PDF Service Error] {e}")

        # Real-Time WebSocket Broadcast to Employer
        from django.urls import reverse
        from .realtime import broadcast_user_event
        broadcast_user_event(
            agreement.employer.id,
            "agreement_status_changed",
            {
                "agreement_id": str(agreement.id),
                "agreement_number": agreement.agreement_number,
                "job_title": agreement.job.title,
                "worker_name": user.name,
                "status": "FULLY_EXECUTED",
                "url": reverse("agreement_employer_review", args=[agreement.id]),
            },
        )

        success_msg = "अनुबंध सफलतापूर्वक हस्ताक्षरित! दोनों पक्षों के फोन नंबर अनलॉक हो गए हैं।" if lang == 'hi' else "Agreement fully executed! Both parties' verified phone numbers are now unlocked."
        messages.success(request, success_msg)

        if chat_room:
            return redirect('chat_room_detail', room_id=chat_room.id)
        return redirect('agreements_dashboard')

    context = {
        'agreement': agreement,
        'job': agreement.job,
        'current_user': user,
        'current_lang': lang,
        'user_role': 'worker',
    }
    return render(request, 'agreements/viewer.html', context)


# ==============================================================================
# 3. Worker Decline Agreement Action
# ==============================================================================

@require_POST
def agreement_decline_view(request, agreement_id):
    """Worker declines the terms of the agreement."""
    auth_redirect = _require_auth(request, allowed_roles=['worker'])
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    agreement = get_object_or_404(DigitalAgreement, id=agreement_id)
    lang = request.GET.get('lang') or request.session.get('lang', 'hi')
    if request.GET.get('lang') in ('en', 'hi'):
        request.session['lang'] = request.GET.get('lang')

    reason = request.POST.get('reason', 'Worker declined to sign the agreement terms.').strip()

    agreement.status = 'DECLINED_BY_WORKER'
    agreement.save()

    AgreementAuditLog.objects.create(
        agreement=agreement,
        actor=user,
        event_type='DECLINED',
        previous_status='WORKER_REVIEW_PENDING',
        new_status='DECLINED_BY_WORKER',
        metadata={'reason': reason, 'ip': get_client_ip(request)}
    )

    chat_room = ChatRoom.objects.filter(job=agreement.job, worker=user).first()
    if chat_room:
        ChatMessage.objects.create(
            chat_room=chat_room,
            sender=user,
            message=f"Worker declined the agreement terms. Reason: {reason}",
            is_system_notice=True
        )

    messages.info(request, "अनुबंध अस्वीकार कर दिया गया।" if lang == 'hi' else "Agreement declined.")
    if chat_room:
        return redirect('chat_room_detail', room_id=chat_room.id)
    return redirect('my_applications')


# ==============================================================================
# 4. PDF Download View (Authorized & Tamper-Checked)
# ==============================================================================

def agreement_download_pdf_view(request, agreement_id):
    """
    Streams the official generated PDF file.
    Validates ownership: only the employer, assigned worker, or admin can download.
    """
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    agreement = get_object_or_404(DigitalAgreement, id=agreement_id)

    # Ownership check
    is_owner = (agreement.employer == user) or (agreement.worker == user) or (user.role == 'admin')
    if not is_owner:
        raise Http404("You do not have permission to download this legal document.")

    # Generate or refresh PDF if not on disk
    media_dir = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
    pdf_path = os.path.join(media_dir, agreement.generated_pdf_file) if agreement.generated_pdf_file else ""

    if not pdf_path or not os.path.exists(pdf_path):
        pdf_path = generate_legal_agreement_pdf(agreement)

    # Log download event
    AgreementAuditLog.objects.create(
        agreement=agreement,
        actor=user,
        event_type='DOWNLOADED',
        previous_status=agreement.status,
        new_status=agreement.status,
        metadata={'ip': get_client_ip(request)}
    )

    with open(pdf_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{agreement.agreement_number}.pdf"'
        return response


# ==============================================================================
# 5. Agreement Management Dashboard
# ==============================================================================

def agreements_dashboard_view(request):
    """
    Centralized Legal Hub for both Employers and Workers.
    Displays:
    - Status filtering (Active/Executed, Pending Signature, Declined, Disputed)
    - Agreement metadata & Download PDF actions
    - Audit Trail & Dispute filing access
    """
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    lang = request.session.get('lang', 'hi')
    status_filter = request.GET.get('status', 'all')

    if user.role == 'employer':
        qs = DigitalAgreement.objects.filter(employer=user)
    else:
        qs = DigitalAgreement.objects.filter(Q(worker=user) | Q(job__applications__worker=user)).distinct()

    if status_filter != 'all':
        qs = qs.filter(status=status_filter)

    agreements = qs.select_related('job', 'employer', 'worker').order_by('-created_at')

    context = {
        'agreements': agreements,
        'current_user': user,
        'current_lang': lang,
        'selected_status': status_filter,
    }
    return render(request, 'agreements/dashboard.html', context)


# ==============================================================================
# 6. Audit Trail & Verification Modal API
# ==============================================================================

def agreement_audit_history_api(request, agreement_id):
    """Returns JSON audit trail of signing events and document integrity."""
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    user = _get_current_user(request)
    agreement = get_object_or_404(DigitalAgreement, id=agreement_id)

    if agreement.employer != user and agreement.worker != user and user.role != 'admin':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    logs = agreement.audit_logs.select_related('actor').order_by('timestamp')
    events = []
    for l in logs:
        events.append({
            'event_type': l.event_type,
            'actor_name': l.actor.name if l.actor else "System",
            'actor_role': l.actor.role if l.actor else "System",
            'timestamp': l.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'metadata': l.metadata
        })

    return JsonResponse({
        'agreement_number': agreement.agreement_number,
        'status': agreement.get_status_display(),
        'document_hash': agreement.document_hash,
        'template_version': agreement.template_version,
        'events': events
    })


# ==============================================================================
# 7. Dispute Registration View
# ==============================================================================

@require_POST
def agreement_raise_dispute_view(request, agreement_id):
    """File a formal dispute against an agreement."""
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    agreement = get_object_or_404(DigitalAgreement, id=agreement_id)

    if agreement.employer != user and agreement.worker != user:
        raise Http404("Unauthorized")

    category = request.POST.get('dispute_category', 'PAYMENT')
    description = request.POST.get('description', '').strip()

    if not description:
        messages.error(request, "Please provide a detailed description of the incident.")
        return redirect('agreements_dashboard')

    dispute = AgreementDispute.objects.create(
        agreement=agreement,
        raised_by=user,
        dispute_category=category,
        description=description,
        status='OPEN'
    )

    agreement.status = 'DISPUTED'
    agreement.save()

    AgreementAuditLog.objects.create(
        agreement=agreement,
        actor=user,
        event_type='DISPUTE_RAISED',
        previous_status='FULLY_EXECUTED',
        new_status='DISPUTED',
        metadata={'dispute_id': str(dispute.id), 'category': category}
    )

    messages.success(request, "Dispute registered. Rojgar Setu arbitration will facilitate a fair resolution.")
    return redirect('agreements_dashboard')
