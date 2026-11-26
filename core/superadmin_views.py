"""
SuperAdmin Control Center Views for Rojgar Setu.
Strictly gated to authenticated users with role == 'admin'.
Provides full platform telemetry, direct user/password manipulation,
job moderation, agreement inspection, and dispute resolution.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    UserAccount, WorkerProfile, Job, Application,
    ChatRoom, DigitalAgreement, AgreementAuditLog, AgreementDispute
)
from .views import _get_current_user


def _require_superadmin(request):
    """Strict SuperAdmin gatekeeper redirecting unauthenticated users to /superadmin/login/."""
    user = _get_current_user(request)
    if not user:
        messages.warning(request, "SuperAdmin authentication required.")
        return redirect('superadmin_login')
    if user.role != 'admin':
        messages.error(request, "Access denied. SuperAdmin privileges required.")
        return redirect('home')
    return None


def superadmin_login_view(request):
    """Dedicated SuperAdmin authentication endpoint (/superadmin/login/)."""
    current = _get_current_user(request)
    if current and current.role == 'admin':
        return redirect('superadmin_dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        admin_user = UserAccount.objects.filter(email__iexact=email, role='admin').first()
        if admin_user and admin_user.check_password(password):
            request.session['rojgar_user_id'] = str(admin_user.id)
            messages.success(request, "Signed in to SuperAdmin Governance Console.")
            return redirect('superadmin_dashboard')

        messages.error(request, "Invalid SuperAdmin email or password.")

    return render(request, 'superadmin/login.html')


def superadmin_dashboard_view(request):
    """Master SuperAdmin Portal with full platform oversight & management tabs."""
    auth_redirect = _require_superadmin(request)
    if auth_redirect:
        return auth_redirect

    admin_user = _get_current_user(request)
    active_tab = request.GET.get('tab', 'users')
    q = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', 'all')

    # Platform Telemetry KPIs
    stats = {
        'total_users': UserAccount.objects.exclude(role='admin').count(),
        'employers_count': UserAccount.objects.filter(role='employer').count(),
        'workers_count': UserAccount.objects.filter(role='worker').count(),
        'verified_users': UserAccount.objects.exclude(role='admin').filter(is_aadhaar_verified=True).count(),
        'active_jobs': Job.objects.filter(is_active=True).exclude(status='draft').count(),
        'draft_jobs': Job.objects.filter(status='draft').count(),
        'total_applications': Application.objects.count(),
        'active_chats': ChatRoom.objects.count(),
        'total_agreements': DigitalAgreement.objects.count(),
        'executed_agreements': DigitalAgreement.objects.filter(status='FULLY_EXECUTED').count(),
        'open_disputes': AgreementDispute.objects.filter(status__in=['OPEN', 'UNDER_REVIEW']).count(),
    }

    # Users Query (Employers & Workers)
    users_qs = UserAccount.objects.select_related('worker_profile').order_by('-created_at')
    if role_filter in ('employer', 'worker', 'admin'):
        users_qs = users_qs.filter(role=role_filter)
    if q:
        users_qs = users_qs.filter(
            Q(name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q) | Q(city__icontains=q)
        )

    # Jobs Query
    jobs_qs = Job.objects.select_related('employer').annotate(
        applicant_count=Count('applications')
    ).order_by('-created_at')[:100]

    # Agreements Query
    agreements_qs = DigitalAgreement.objects.select_related('employer', 'worker', 'job').order_by('-created_at')[:100]

    # Disputes Query
    disputes_qs = AgreementDispute.objects.select_related('agreement', 'raised_by').order_by('-created_at')

    # Recent Audit Logs
    audit_logs = AgreementAuditLog.objects.select_related('agreement', 'actor').order_by('-timestamp')[:50]

    context = {
        'current_user': admin_user,
        'stats': stats,
        'active_tab': active_tab,
        'q': q,
        'role_filter': role_filter,
        'users_list': users_qs[:150],
        'jobs_list': jobs_qs,
        'agreements_list': agreements_qs,
        'disputes_list': disputes_qs,
        'audit_logs': audit_logs,
    }
    return render(request, 'superadmin/dashboard.html', context)


def superadmin_user_edit_view(request, user_id):
    """
    Directly inspect and manipulate any Employer or Worker's data,
    verification flags, worker profile, and reset/update their password.
    """
    auth_redirect = _require_superadmin(request)
    if auth_redirect:
        return auth_redirect

    admin_user = _get_current_user(request)
    target_user = get_object_or_404(UserAccount, id=user_id)
    worker_profile = getattr(target_user, 'worker_profile', None)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', target_user.role)
        city = request.POST.get('city', '').strip()
        locality = request.POST.get('locality', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        preferred_lang = request.POST.get('preferred_lang', target_user.preferred_lang)
        is_phone_verified = request.POST.get('is_phone_verified') == 'on'
        is_aadhaar_verified = request.POST.get('is_aadhaar_verified') == 'on'
        new_password = request.POST.get('new_password', '').strip()

        if not name or not phone:
            messages.error(request, "Name and Phone Number are required.")
            return redirect('superadmin_user_edit', user_id=target_user.id)

        # Check duplicate phone if changed
        if phone != target_user.phone and UserAccount.objects.filter(phone=phone).exclude(id=target_user.id).exists():
            messages.error(request, f"Another account already uses phone {phone}.")
            return redirect('superadmin_user_edit', user_id=target_user.id)

        target_user.name = name
        target_user.phone = phone
        target_user.email = email or None
        if role in ('worker', 'employer', 'admin'):
            target_user.role = role
        target_user.city = city
        target_user.locality = locality
        target_user.pincode = pincode
        if preferred_lang in ('en', 'hi'):
            target_user.preferred_lang = preferred_lang
        target_user.is_phone_verified = is_phone_verified
        target_user.is_aadhaar_verified = is_aadhaar_verified

        if new_password:
            if len(new_password) < 6:
                messages.error(request, "New password must be at least 6 characters.")
                return redirect('superadmin_user_edit', user_id=target_user.id)
            target_user.set_password(new_password)

        target_user.save()

        # Update WorkerProfile if applicable
        if target_user.role == 'worker' and worker_profile:
            primary_trade = request.POST.get('primary_trade', '').strip()
            trades_raw = request.POST.get('trades_csv', '').strip()
            expected_wage = request.POST.get('expected_wage', '').strip()
            wage_type = request.POST.get('wage_type', worker_profile.wage_type)
            ai_bio = request.POST.get('ai_bio', '').strip()

            if primary_trade:
                worker_profile.primary_trade = primary_trade
            if trades_raw:
                worker_profile.trades = [t.strip() for t in trades_raw.split(',') if t.strip()][:4]
            if expected_wage:
                try:
                    worker_profile.expected_wage = float(expected_wage)
                except ValueError:
                    pass
            if wage_type in ('daily', 'monthly', 'per_job'):
                worker_profile.wage_type = wage_type
            worker_profile.ai_bio = ai_bio
            worker_profile.save()

        pwd_note = " Password updated." if new_password else ""
        messages.success(request, f"Updated {target_user.name} ({target_user.role}) successfully.{pwd_note}")
        return redirect('superadmin_dashboard')

    context = {
        'current_user': admin_user,
        'target_user': target_user,
        'worker_profile': worker_profile,
        'trades_csv': ", ".join(worker_profile.trades) if worker_profile and worker_profile.trades else "",
    }
    return render(request, 'superadmin/edit_user.html', context)


@require_POST
def superadmin_user_delete_view(request, user_id):
    """Deletes an employer or worker account (prevents self-deletion)."""
    auth_redirect = _require_superadmin(request)
    if auth_redirect:
        return auth_redirect

    admin_user = _get_current_user(request)
    target_user = get_object_or_404(UserAccount, id=user_id)

    if target_user.id == admin_user.id:
        messages.error(request, "You cannot delete the active SuperAdmin account.")
        return redirect('superadmin_dashboard')

    name = target_user.name
    target_user.delete()
    messages.success(request, f"Account '{name}' and its associated records were permanently deleted.")
    return redirect('superadmin_dashboard')


@require_POST
def superadmin_job_action_view(request, job_id):
    """SuperAdmin moderation actions on any job (activate, pause, close, delete)."""
    auth_redirect = _require_superadmin(request)
    if auth_redirect:
        return auth_redirect

    job = get_object_or_404(Job, id=job_id)
    action = request.POST.get('action', '')

    if action == 'activate':
        job.is_active = True
        job.status = 'active'
        job.save(update_fields=['is_active', 'status'])
        messages.success(request, f"Job '{job.title}' is now Active.")
    elif action == 'pause':
        job.is_active = False
        job.status = 'draft'
        job.save(update_fields=['is_active', 'status'])
        messages.info(request, f"Job '{job.title}' moved to Draft/Paused.")
    elif action == 'close':
        job.is_active = False
        job.status = 'closed'
        job.save(update_fields=['is_active', 'status'])
        messages.info(request, f"Job '{job.title}' marked Closed.")
    elif action == 'delete':
        title = job.title
        job.delete()
        messages.success(request, f"Job '{title}' deleted.")

    return redirect('/superadmin/?tab=jobs')


@require_POST
def superadmin_dispute_update_view(request, dispute_id):
    """Allows SuperAdmin to review and resolve platform agreement disputes."""
    auth_redirect = _require_superadmin(request)
    if auth_redirect:
        return auth_redirect

    dispute = get_object_or_404(AgreementDispute, id=dispute_id)
    new_status = request.POST.get('status', dispute.status)
    resolution_notes = request.POST.get('resolution_notes', '').strip()

    if new_status in ('OPEN', 'UNDER_REVIEW', 'RESOLVED', 'ESCALATED'):
        dispute.status = new_status
        if new_status == 'RESOLVED' and not dispute.resolved_at:
            dispute.resolved_at = timezone.now()
    dispute.resolution_notes = resolution_notes
    dispute.save()

    messages.success(request, f"Dispute for Agreement {dispute.agreement.agreement_number} updated to {dispute.status}.")
    return redirect('/superadmin/?tab=disputes')
