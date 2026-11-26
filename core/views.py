"""
Views for Rojgar Setu (Master Full-Stack P2P Architecture v5.5).
Implements the 5-Stage Pre-Signed Contract Handshake & Dual-Signature Phone Unlock Pipeline:
Stage 1: Job Creation + 1st-Party Pre-Signature
Stage 2: Hyperlocal Discovery & 1-Click Apply
Stage 3: Masked 1-on-1 In-App Chat (Phone & Email Shielded)
Stage 4: In-Chat Contract Forwarding
Stage 5: Worker Counter-Signature -> Fully Executed -> Mutual Phone Numbers Unlocked!
"""

import json
import re
import io
import base64
from PIL import Image
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Q, Count, Sum

from .models import (
    UserAccount, WorkerProfile, Job, Application,
    ChatRoom, ChatMessage, Contract, Category
)
from .forms import (
    WorkerRegisterForm, EmployerRegisterForm, LoginForm,
    JobCreateForm
)
from .ai_service import (
    generate_multi_category_assessment,
    generate_dynamic_contract_terms,
    generate_worker_ai_bio,
    FALLBACK_TRADE_QUESTIONS,
    get_trade_questions_bank
)
from .spatial import (
    get_hyperlocal_jobs,
    get_hyperlocal_workers,
    calculate_haversine_distance,
    format_distance
)


# ==============================================================================
# Authentication & Session Helpers
# ==============================================================================

def _get_current_user(request):
    """Retrieves authenticated UserAccount instance from session (cached per-request)."""
    if hasattr(request, '_rojgar_cached_user'):
        return request._rojgar_cached_user
    user_id = request.session.get('rojgar_user_id')
    user = None
    if user_id:
        try:
            user = UserAccount.objects.get(id=user_id)
        except UserAccount.DoesNotExist:
            request.session.flush()
    request._rojgar_cached_user = user
    return user


def _require_auth(request, allowed_roles=None):
    """Auth gatekeeper. Redirects to login if unauthenticated or unauthorized."""
    user = _get_current_user(request)
    if not user:
        messages.warning(request, "Please log in to access this page / कृपया आगे बढ़ने के लिए लॉगिन करें।")
        return redirect('login')
    if allowed_roles and user.role not in allowed_roles:
        messages.error(request, "Access restricted for your profile type.")
        return redirect('home')
    return None


# ==============================================================================
# Landing & Discover
# ==============================================================================

def ensure_webp_data_url(data_str, max_dimension=512, quality=88):
    """Ensures profile picture is stored in optimized, high-fidelity WebP format."""
    if not data_str or not isinstance(data_str, str):
        return data_str

    if data_str.startswith('data:image/webp;base64,'):
        return data_str

    try:
        if ',' in data_str:
            _, encoded = data_str.split(',', 1)
        else:
            encoded = data_str

        image_bytes = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(image_bytes))

        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            image = image.convert('RGBA')
        else:
            image = image.convert('RGB')

        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        image.save(buffer, format='WEBP', quality=quality, method=4)
        webp_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/webp;base64,{webp_b64}"
    except Exception as e:
        print(f"[Image Conversion to WebP Warning]: {e}")
        return data_str


def home_view(request):
    """
    Rojgar Setu Landing Page:
    - P2P Paradigm Showcase (Zero Agency Brokerage)
    - Hyperlocal Leaflet Map with Active Gigs
    - 5-Stage Contract Handshake Infographic
    - Real-Time Platform Stats
    """
    current_user = _get_current_user(request)
    
    # Platform metrics
    total_jobs = Job.objects.filter(is_active=True).count()
    total_workers = WorkerProfile.objects.filter(is_available=True).count()
    total_contracts = Contract.objects.filter(status='active').count()
    total_savings = total_contracts * 18000  # Estimate ₹18,000 agency fee saved per hire!

    # Hyperlocal Job Feed
    user_lat = current_user.latitude if current_user and current_user.latitude else 28.6280
    user_lng = current_user.longitude if current_user and current_user.longitude else 77.3649
    nearby_jobs = get_hyperlocal_jobs(user_lat, user_lng, max_radius_km=10.0)[:6]

    # Map Pins Data for Leaflet.js
    map_pins = []
    for j in nearby_jobs:
        if j.latitude and j.longitude:
            map_pins.append({
                'id': str(j.id),
                'title': j.title,
                'category': j.category,
                'price': float(j.offered_price),
                'duration': j.duration_text,
                'city': j.city,
                'locality': j.locality,
                'lat': j.latitude,
                'lng': j.longitude,
                'distance': getattr(j, 'distance_display', 'Nearby')
            })

    categories = Category.objects.all().order_by('name_en')

    context = {
        'current_user': current_user,
        'total_jobs': total_jobs,
        'total_workers': total_workers,
        'total_contracts': total_contracts,
        'total_savings': total_savings,
        'nearby_jobs': nearby_jobs,
        'map_pins': map_pins,
        'categories': categories,
    }
    return render(request, 'index.html', context)


# ==============================================================================
# Registration & Authentication
# ==============================================================================

def register_view(request):
    """Landing registration screen allowing choice between Worker and Employer."""
    if _get_current_user(request):
        return redirect('home')
    return render(request, 'auth/register.html')


def reverse_geocode_coordinates(latitude: float, longitude: float) -> tuple[str, str]:
    """
    Reverse geocodes latitude/longitude into (locality, city)
    using BigDataCloud and OpenStreetMap with fallback to coordinates.
    """
    if not latitude or not longitude:
        return "Local Area", "India"

    try:
        url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={latitude}&longitude={longitude}&localityLanguage=en"
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            locality = (
                data.get("locality")
                or (data.get("localityInfo", {}).get("administrative", [{}])[-1].get("name") if data.get("localityInfo", {}).get("administrative") else "")
                or "Local Area"
            )
            city = data.get("city") or data.get("principalSubdivision") or "India"
            if locality and city:
                return locality, city
    except Exception:
        pass

    try:
        headers = {"User-Agent": "RojgarSetuApp/1.0 (contact@rojgarsetu.local)"}
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
        resp = requests.get(url, headers=headers, timeout=3)
        if resp.status_code == 200:
            addr = resp.json().get("address", {})
            locality = addr.get("suburb") or addr.get("village") or addr.get("town") or addr.get("county") or "Local Area"
            city = addr.get("city") or addr.get("state_district") or addr.get("state") or "India"
            if locality and city:
                return locality, city
    except Exception:
        pass

    return f"GPS ({latitude:.2f}° N)", f"GPS ({longitude:.2f}° E)"


def register_worker_view(request):
    """
    Unified 4-Part Karigar Registration Wizard:
    1. Basic Details: Name, Mobile, Email, Password, GPS Location
    2. Vocational Trades: 10 fields in staggered pill layout (Screenshot 2), up to 4 selections
    3. Gemini Flash AI Skill Assessment Quiz (with dynamic rating & bio synthesis)
    4. Mock DigiLocker Identity Verification (Government ID Verified seal)
    Creates the fully verified candidate profile and redirects to the profile showcase.
    """
    if _get_current_user(request):
        return redirect('home')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip().replace(' ', '').replace('-', '')
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        try:
            latitude = float(request.POST.get('latitude') or 28.6280)
            longitude = float(request.POST.get('longitude') or 77.3649)
        except ValueError:
            latitude, longitude = 28.6280, 77.3649

        city = request.POST.get('city', '').strip()
        locality = request.POST.get('locality', '').strip()

        # Extract authentic location directly from coordinates if not manually typed
        if (not city or city == 'Noida') and latitude and longitude:
            extracted_loc, extracted_ct = reverse_geocode_coordinates(latitude, longitude)
            if extracted_ct and extracted_ct != 'India':
                city = extracted_ct
                locality = extracted_loc
            elif not city:
                city = 'Noida'
                locality = 'Sector 62'

        # Trades selection
        selected_trades = request.POST.getlist('trades')
        if not selected_trades:
            raw_trades = request.POST.get('selected_trades_str', '')
            if raw_trades:
                selected_trades = [t.strip() for t in raw_trades.split(',') if t.strip()]
        if not selected_trades:
            selected_trades = ['Electrician']
        selected_trades = selected_trades[:4]

        try:
            experience_years = int(request.POST.get('experience_years') or 2)
        except ValueError:
            experience_years = 2

        try:
            expected_wage = float(request.POST.get('expected_wage') or 500)
        except ValueError:
            expected_wage = 500.0

        wage_type = request.POST.get('wage_type', 'daily')

        # Basic validations
        errors = []
        if not name:
            errors.append("Please enter your full name.")
        if not re.search(r'^[6-9]\d{9}$', phone):
            errors.append("Please enter a valid 10-digit Indian mobile number.")
        elif UserAccount.objects.filter(phone=phone).exists():
            errors.append("An account with this phone number already exists.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")

        lang = request.session.get('django_language', 'en')
        questions_bank = get_trade_questions_bank(lang)

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'auth/register_worker.html', {
                'questions_json': json.dumps(questions_bank, ensure_ascii=False),
                'form_data': request.POST,
                'errors': errors
            })

        # Calculate Quiz Score
        try:
            total_questions = int(request.POST.get('quiz_total_questions', 0) or 4)
        except ValueError:
            total_questions = 4
        score = 0
        for i in range(1, total_questions + 1):
            user_ans = request.POST.get(f'quiz_answer_{i}')
            correct_ans = request.POST.get(f'quiz_correct_{i}')
            if user_ans is not None and str(user_ans) == str(correct_ans):
                score += 1

        # DigiLocker verification status
        digilocker_verified = request.POST.get('digilocker_verified', 'false').lower() == 'true'

        # Profile Picture (Saved in optimized WebP format)
        profile_picture_data = ensure_webp_data_url(request.POST.get('profile_picture_data', '').strip())

        # Create Core User
        user = UserAccount(
            name=name,
            phone=phone,
            email=email,
            role='worker',
            profile_picture=profile_picture_data,
            preferred_lang='hi',
            latitude=latitude,
            longitude=longitude,
            city=city,
            locality=locality,
            is_aadhaar_verified=digilocker_verified
        )
        user.set_password(password)
        user.save()

        # Generate Detailed AI Bio via Gemini Flash (Strictly verified data: trades + quiz score)
        score_pct = int((score / max(total_questions, 1)) * 100)
        ai_bio = generate_worker_ai_bio(
            name=user.name,
            trades=selected_trades,
            score=score,
            total_mcqs=total_questions,
            language='en'
        )

        # Create Worker Profile
        karigar_code = f"RS-IND-{user.phone[-4:]}"
        badges = {
            'aadhaar_verified': digilocker_verified,
            'mcq_passed': score >= max(1, total_questions // 2),
            'mcq_score': f"{score}/{total_questions}",
            'skill_badge': "Skills Tested ★" if score >= 2 else "Verified Artisan",
            'score_pct': score_pct,
            'digilocker_token': f"DL-AADH-2026-{user.phone[-4:]}"
        }

        profile = WorkerProfile.objects.create(
            user=user,
            karigar_id=karigar_code,
            trades=selected_trades,
            primary_trade=selected_trades[0],
            experience_years=experience_years,
            expected_wage=expected_wage,
            wage_type=wage_type,
            latitude=user.latitude,
            longitude=user.longitude,
            city=user.city,
            locality=user.locality,
            ai_bio=ai_bio,
            verification_badges=badges
        )

        # Auto-login to session
        request.session['rojgar_user_id'] = str(user.id)
        messages.success(request, f"Welcome {user.name}! Your verified Karigar profile has been created with Gemini AI rating and DigiLocker ID verification.")
        return redirect('worker_profile')

    # GET request
    lang = request.session.get('django_language', 'en')
    questions_bank = get_trade_questions_bank(lang)
    return render(request, 'auth/register_worker.html', {
        'questions_json': json.dumps(questions_bank, ensure_ascii=False),
    })


def register_employer_view(request):
    """
    Homeowner / Employer Registration:
    - Captures exact GPS Coordinates for job dispatch
    - Supports in-situ profile photo capture with WebP conversion
    - 2-Step Registration Wizard with dedicated DigiLocker Aadhaar Verification step
    """
    if _get_current_user(request):
        return redirect('home')

    lang = request.session.get('lang', 'hi')

    if request.method == 'POST':
        form = EmployerRegisterForm(request.POST, lang=lang)
        if form.is_valid():
            data = form.cleaned_data
            
            raw_photo = (data.get('profile_picture_data') or request.POST.get('profile_picture_data') or '').strip()
            profile_picture = ensure_webp_data_url(raw_photo) if raw_photo else ''

            latitude = data.get('latitude') or 28.6280
            longitude = data.get('longitude') or 77.3649
            city = data.get('city') or ''
            locality = data.get('locality') or ''

            # Extract authentic location directly from coordinates if not manually set
            if (not city or city == 'Noida') and latitude and longitude:
                extracted_loc, extracted_ct = reverse_geocode_coordinates(latitude, longitude)
                if extracted_ct and extracted_ct != 'India':
                    city = extracted_ct
                    locality = extracted_loc
                elif not city:
                    city = 'Noida'
                    locality = 'Sector 62'

            digilocker_verified = (
                request.POST.get('digilocker_verified') == 'true' or 
                data.get('digilocker_verified') is True or 
                data.get('digilocker_consent') is True
            )

            user = UserAccount(
                name=data['name'],
                phone=data['phone'],
                email=data.get('email', ''),
                role='employer',
                profile_picture=profile_picture,
                is_aadhaar_verified=digilocker_verified,  # Verified via DigiLocker step
                latitude=latitude,
                longitude=longitude,
                city=city,
                locality=locality,
            )
            user.set_password(data['password'])
            user.save()

            request.session['rojgar_user_id'] = str(user.id)
            messages.success(request, f"Welcome {user.name}! Your employer account is verified.")
            return redirect('employer_profile')
    else:
        form = EmployerRegisterForm(lang=lang)

    return render(request, 'auth/register_employer.html', {'form': form})


def login_view(request):
    """Login using 10-digit Indian mobile number or registered email address."""
    if _get_current_user(request):
        return redirect('home')

    lang = request.session.get('lang', 'hi')

    if request.method == 'POST':
        form = LoginForm(request.POST, lang=lang)
        if form.is_valid():
            raw_identifier = form.cleaned_data['phone'].strip()
            password = form.cleaned_data['password']

            if '@' in raw_identifier:
                # Email login: preserve hyphens/dots, match case-insensitively
                user = UserAccount.objects.filter(email__iexact=raw_identifier.lower()).first()
            else:
                # Mobile login: normalize spaces, dashes, and optional +91 prefix
                digits = re.sub(r'\D', '', raw_identifier)
                if len(digits) > 10 and digits.startswith('91'):
                    digits = digits[-10:]
                user = UserAccount.objects.filter(phone=digits).first()

            if user:
                if user.check_password(password):
                    request.session['rojgar_user_id'] = str(user.id)
                    messages.success(request, f"Welcome back, {user.name}!")
                    if user.role == 'admin':
                        return redirect('superadmin_dashboard')
                    if user.role == 'worker':
                        return redirect('worker_profile')
                    return redirect('employer_profile')
                else:
                    messages.error(
                        request,
                        "गलत पासवर्ड। कृपया पुनः प्रयास करें।" if lang == 'hi' else "Incorrect password. Please try again."
                    )
            else:
                messages.error(
                    request,
                    "इस मोबाइल नंबर या ईमेल से कोई खाता नहीं मिला।" if lang == 'hi' else "Account not found with this mobile number or email."
                )
    else:
        form = LoginForm(lang=lang)

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    """Logs out user and clears session."""
    request.session.flush()
    messages.info(request, "You have been logged out.")
    return redirect('home')


# ==============================================================================
# Dynamic AI Assessment (Gemini Flash)
# ==============================================================================

def ai_assessment_view(request):
    """
    AI Skill Assessment & Auto-Scoring:
    - Generates 4-6 MCQs across the worker's selected 1 to 4 trades
    - Auto-grades submission
    - Synthesizes AI Profile Bio
    - Awards 'Skills Tested ★' Badge
    """
    user = _get_current_user(request)
    if not user or user.role != 'worker':
        return redirect('home')

    try:
        profile = user.worker_profile
    except WorkerProfile.DoesNotExist:
        messages.error(request, "Worker profile not found.")
        return redirect('home')

    if request.method == 'POST':
        # Grade submitted MCQs
        total_questions = int(request.POST.get('total_questions', 0))
        score = 0
        
        for i in range(1, total_questions + 1):
            user_ans = request.POST.get(f'question_{i}')
            correct_ans = request.POST.get(f'correct_{i}')
            if user_ans is not None and str(user_ans) == str(correct_ans):
                score += 1

        # Synthesize AI Bio via Gemini
        ai_bio = generate_worker_ai_bio(
            name=user.name,
            trades=profile.trades,
            experience_years=profile.experience_years,
            score=score,
            total_mcqs=total_questions,
            language=user.preferred_lang
        )

        # Update profile badges
        profile.ai_bio = ai_bio
        badges = profile.verification_badges or {}
        badges['mcq_passed'] = score >= (total_questions // 2)
        badges['mcq_score'] = f"{score}/{total_questions}"
        badges['skill_badge'] = "Skills Tested ★"
        badges['score_pct'] = int((score / max(total_questions, 1)) * 100)
        profile.verification_badges = badges
        profile.save()

        messages.success(request, f"Assessment Complete! You scored {score}/{total_questions}. Your AI profile is live!")
        return redirect('worker_profile')

    # GET: Generate questions
    trades = profile.trades or [profile.primary_trade or 'Electrician']
    questions = generate_multi_category_assessment(trades, language=user.preferred_lang)

    context = {
        'user': user,
        'profile': profile,
        'trades': trades,
        'questions': questions,
        'total_questions': len(questions),
    }
    return render(request, 'quiz/assessment.html', context)


# ==============================================================================
# Hyperlocal Jobs & Pre-Signed Contracts
# ==============================================================================

def jobs_list_view(request):
    """
    Hyperlocal Job Feed:
    - Distance-sorted within 500m - 10km
    - Trade filter
    - Displays Pre-Signed Contract Badge
    - 1-Click Apply
    """
    user = _get_current_user(request)
    category = request.GET.get('category', 'all')

    user_lat = user.latitude if user and user.latitude else 28.6280
    user_lng = user.longitude if user and user.longitude else 77.3649

    jobs = get_hyperlocal_jobs(user_lat, user_lng, category=category, max_radius_km=10.0)
    categories = Category.objects.all().order_by('name_en')

    # Get user's applied job IDs to show application state
    applied_job_ids = set()
    if user and user.role == 'worker':
        applied_job_ids = set(Application.objects.filter(worker=user).values_list('job_id', flat=True))

    context = {
        'current_user': user,
        'jobs': jobs,
        'selected_category': category,
        'categories': categories,
        'applied_job_ids': applied_job_ids,
    }
    return render(request, 'jobs/list.html', context)


def job_detail_view(request, job_id):
    """Job detail view displaying terms, pay, employer badge, and pre-signed contract stamp."""
    job = get_object_or_404(Job, id=job_id)
    user = _get_current_user(request)

    distance_display = "Nearby"
    if user and user.latitude and user.longitude and job.latitude and job.longitude:
        dist = calculate_haversine_distance(user.latitude, user.longitude, job.latitude, job.longitude)
        distance_display = format_distance(dist)

    has_applied = False
    application = None
    if user and user.role == 'worker':
        application = Application.objects.filter(job=job, worker=user).first()
        has_applied = bool(application)

    # Fetch associated digital agreement
    agreement = job.latest_agreement
    is_owner = bool(user and user.id == job.employer.id)

    context = {
        'job': job,
        'current_user': user,
        'is_owner': is_owner,
        'distance_display': distance_display,
        'has_applied': has_applied,
        'application': application,
        'agreement': agreement,
    }
    return render(request, 'jobs/detail.html', context)


def job_create_view(request):
    """
    Job Creation with Dynamic Contract Generator & 1st-Party Digital Pre-Signing.
    Employer digitally signs upfront as First Party!
    """
    auth_redirect = _require_auth(request, allowed_roles=['employer', 'admin'])
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    lang = request.GET.get('lang') or request.session.get('lang', 'hi')
    if request.GET.get('lang') in ('en', 'hi'):
        request.session['lang'] = request.GET.get('lang')

    # Detect any unfinished database draft for this employer
    db_draft = Job.objects.filter(employer=user, status='draft', is_active=False).order_by('-created_at').first()
    resume_job_id = request.GET.get('resume_job')
    if resume_job_id:
        target_draft = Job.objects.filter(id=resume_job_id, employer=user, status='draft').first()
        if target_draft:
            db_draft = target_draft

    if request.method == 'POST':
        form = JobCreateForm(request.POST, lang=lang)
        if form.is_valid():
            data = form.cleaned_data

            # 1. Create Job in DRAFT / UNPUBLISHED state (is_active=False)
            job = Job.objects.create(
                employer=user,
                title=data['title'],
                category=data['category'],
                responsibilities=data.get('responsibilities') or data['title'],
                duration_text=data['duration_text'],
                offered_price=data['offered_price'],
                wage_period=data['wage_period'],
                city=data.get('city') or user.city,
                locality=data.get('locality') or user.locality,
                latitude=data.get('latitude') or user.latitude or 28.6280,
                longitude=data.get('longitude') or user.longitude or 77.3649,
                contract_terms=data.get('contract_terms', ''),
                employer_signature='',
                is_active=False,
                status='draft'
            )

            # 2. Compile Category-Specific Digital Agreement
            from .agreement_engine import compile_canonical_agreement_text, generate_agreement_number
            from .models import DigitalAgreement, AgreementAuditLog

            agr_num = generate_agreement_number(job.category, str(job.id)[:8])
            canonical_txt, doc_hash, rendered_html = compile_canonical_agreement_text(
                agreement_number=agr_num,
                employer_name=user.name,
                employer_phone=user.phone,
                worker_name="",
                worker_phone="",
                job_title=job.title,
                category=job.category,
                scope_of_work=job.responsibilities,
                locality=job.locality,
                city=job.city,
                offered_price=float(job.offered_price),
                wage_period=job.wage_period,
                duration_text=job.duration_text,
                lang=lang
            )

            agreement = DigitalAgreement.objects.create(
                agreement_number=agr_num,
                job=job,
                employer=user,
                category=job.category,
                status='EMPLOYER_REVIEW_PENDING',
                job_data_snapshot={
                    'title': job.title,
                    'category': job.category,
                    'price': float(job.offered_price),
                    'wage_period': job.wage_period,
                    'duration': job.duration_text,
                    'locality': job.locality,
                    'city': job.city
                },
                compiled_agreement_html=rendered_html,
                compiled_agreement_text=canonical_txt,
                document_hash=doc_hash
            )

            # Log audit event
            AgreementAuditLog.objects.create(
                agreement=agreement,
                actor=user,
                event_type='CREATED',
                previous_status='DRAFT',
                new_status='EMPLOYER_REVIEW_PENDING',
                metadata={'job_id': str(job.id), 'category': job.category}
            )

            # 3. Redirect Employer to Agreement Review & Signature Capture Screen
            return redirect('agreement_employer_review', agreement_id=agreement.id)
    else:
        init_locality = user.locality or ''
        init_city = user.city or ''
        if init_locality.startswith('GPS (') or '°' in init_locality:
            init_locality = ''
        if init_city.startswith('GPS (') or '°' in init_city:
            init_city = ''

        initial_vals = {
            'city': init_city,
            'locality': init_locality,
        }

        # If resuming a specific database draft
        if db_draft and resume_job_id:
            initial_vals['title'] = db_draft.title
            initial_vals['category'] = db_draft.category
            initial_vals['responsibilities'] = db_draft.responsibilities
            initial_vals['offered_price'] = db_draft.offered_price
            initial_vals['wage_period'] = db_draft.wage_period
            initial_vals['locality'] = db_draft.locality
            initial_vals['city'] = db_draft.city
            initial_vals['duration_text'] = db_draft.duration_text

        form = JobCreateForm(initial=initial_vals, lang=lang)

    return render(request, 'jobs/create.html', {
        'form': form,
        'current_user': user,
        'db_draft': db_draft
    })


def job_delete_draft_view(request, job_id):
    """Allows employer to discard an unfinished draft job."""
    user = _get_current_user(request)
    if not user:
        return redirect('login')
    draft = get_object_or_404(Job, id=job_id, employer=user, status='draft')
    draft.delete()
    messages.success(request, "Draft job discarded successfully.")
    return redirect('employer_profile')


@require_POST
def job_toggle_status_view(request, job_id):
    """Allows an employer to close an active job opening (blocking new worker applications) or reopen it."""
    auth_redirect = _require_auth(request, allowed_roles=['employer', 'admin'])
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    job = get_object_or_404(Job, id=job_id, employer=user)

    if job.status == 'draft':
        messages.warning(request, "Draft jobs must be signed and published before they can be closed or reopened.")
    elif job.is_active and job.status == 'active':
        job.status = 'closed'
        job.is_active = False
        job.save(update_fields=['status', 'is_active'])
        messages.success(request, f"\"{job.title}\" is now closed. Workers can no longer apply to this opening.")
    else:
        job.status = 'active'
        job.is_active = True
        job.save(update_fields=['status', 'is_active'])
        messages.success(request, f"\"{job.title}\" has been reopened and is accepting worker applications again.")

    next_url = (request.POST.get('next') or '').strip()
    if next_url.startswith('/') and not next_url.startswith('//'):
        return redirect(next_url)
    return redirect('employer_profile')


def my_jobs_view(request):
    """Employer dashboard showing published and closed jobs (no drafts), applicant counts, and chat links."""
    auth_redirect = _require_auth(request, allowed_roles=['employer', 'admin'])
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    jobs = Job.objects.filter(employer=user).exclude(status='draft').prefetch_related('digital_agreements').annotate(
        applicant_count=Count('applications')
    ).order_by('-created_at')

    return render(request, 'jobs/my_jobs.html', {'jobs': jobs, 'current_user': user})


@require_POST
def apply_job_view(request, job_id):
    """Worker 1-Click Apply with AI Score & Verified Badges."""
    auth_redirect = _require_auth(request, allowed_roles=['worker'])
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    job = get_object_or_404(Job, id=job_id)
    if not job.is_active or job.status != 'active':
        messages.warning(request, "This job opening has been closed by the employer and is no longer accepting applications.")
        return redirect('job_detail', job_id=job.id)

    # Check if already applied
    app, created = Application.objects.get_or_create(
        job=job,
        worker=user,
        defaults={
            'fit_score': 90.0,
            'status': 'applied',
            'notes': 'Applied via Rojgar Setu Hyperlocal 1-Click Rail'
        }
    )

    if created:
        # Real-Time WebSocket Broadcast to Employer
        from django.urls import reverse
        from .realtime import broadcast_user_event
        wp = getattr(user, 'worker_profile', None)
        dist_str = "Nearby"
        if user.latitude and user.longitude and job.latitude and job.longitude:
            d = calculate_haversine_distance(user.latitude, user.longitude, job.latitude, job.longitude)
            dist_str = format_distance(d)

        broadcast_user_event(
            job.employer.id,
            "job_application_created",
            {
                "job_id": str(job.id),
                "job_title": job.title,
                "application_id": str(app.id),
                "applicant_count": job.applications.count(),
                "worker_name": user.name,
                "worker_avatar": user.avatar_url,
                "worker_verified": bool(user.is_aadhaar_verified),
                "worker_score": (wp.verification_badges or {}).get("mcq_score", "5/5") if wp else "5/5",
                "worker_trades": ", ".join(wp.trades or []) if wp else job.category,
                "worker_bio": wp.ai_bio if wp else "",
                "distance_display": dist_str,
                "applicants_url": reverse("job_applicants", args=[job.id]),
                "initiate_chat_url": reverse("initiate_chat", args=[app.id]),
            },
        )
        messages.success(request, f"Application submitted to {job.employer.name}! You will be notified when chat opens.")
    else:
        messages.info(request, "You have already applied for this opening.")

    return redirect('job_detail', job_id=job.id)


def job_applicants_view(request, job_id):
    """
    Employer reviews applicants for their job:
    - AI Score & AI Bio
    - Proximity to job location
    - Mutually signed contracts / downloadable agreements for this specific job opening
    """
    auth_redirect = _require_auth(request, allowed_roles=['employer', 'admin'])
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    job = get_object_or_404(Job, id=job_id, employer=user)
    applications = list(
        Application.objects.filter(job=job)
        .select_related('worker', 'worker__worker_profile', 'chat_room', 'chat_room__contract')
        .order_by('-applied_at')
    )

    from .models import DigitalAgreement
    executed_agreements = list(
        DigitalAgreement.objects.filter(job=job, status='FULLY_EXECUTED')
        .select_related('worker')
        .order_by('-worker_signed_at', '-created_at')
    )
    agreements_by_worker = {a.worker_id: a for a in executed_agreements if a.worker_id}
    fallback_agreement = job.latest_agreement

    accepted_contracts = list(
        Contract.objects.filter(job=job, status__in=['active', 'completed'])
        .select_related('worker', 'chat_room')
        .order_by('-worker_signed_at', '-created_at')
    )
    for c in accepted_contracts:
        agr = agreements_by_worker.get(c.worker_id) or (
            fallback_agreement if fallback_agreement and fallback_agreement.status == 'FULLY_EXECUTED' else None
        )
        c.download_agreement_id = agr.id if agr else None

    # Attach proximity & contract/agreement state to each applicant
    for app in applications:
        w = app.worker
        if w.latitude and w.longitude and job.latitude and job.longitude:
            dist = calculate_haversine_distance(job.latitude, job.longitude, w.latitude, w.longitude)
            app.distance_display = format_distance(dist)
        else:
            app.distance_display = "Nearby"

        chat_room = getattr(app, 'chat_room', None)
        contract = getattr(chat_room, 'contract', None) if chat_room else None
        app.signed_contract = contract if (contract and contract.status in ('active', 'completed')) else None
        agr = agreements_by_worker.get(w.id) or (
            fallback_agreement if (app.signed_contract and fallback_agreement and fallback_agreement.status == 'FULLY_EXECUTED') else None
        )
        app.download_agreement_id = agr.id if agr else None

    context = {
        'job': job,
        'applications': applications,
        'accepted_contracts': accepted_contracts,
        'current_user': user,
    }
    return render(request, 'jobs/applicants.html', context)


# ==============================================================================
# In-App 1-on-1 Chat & Pre-Signed Contract Handshake
# ==============================================================================

def initiate_chat_view(request, app_id):
    """
    Employer accepts an applicant -> Opens In-App Masked Chat Room.
    Application status transitions to 'chat_initiated'.
    """
    auth_redirect = _require_auth(request, allowed_roles=['employer', 'admin'])
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    app = get_object_or_404(Application, id=app_id, job__employer=user)

    app.status = 'chat_initiated'
    app.save()

    # Get or create chat room
    room, created = ChatRoom.objects.get_or_create(
        application=app,
        job=app.job,
        employer=user,
        worker=app.worker
    )

    if created:
        ChatMessage.objects.create(
            chat_room=room,
            sender=user,
            message=f"Hello {app.worker.name}! I have reviewed your profile and verified test score for '{app.job.title}'. Let's discuss.",
            is_system_notice=False
        )

    # Real-Time WebSocket Broadcast to Worker
    from django.urls import reverse
    from .realtime import broadcast_user_event
    broadcast_user_event(
        app.worker.id,
        "application_accepted",
        {
            "application_id": str(app.id),
            "job_id": str(app.job.id),
            "job_title": app.job.title,
            "employer_name": user.name,
            "employer_avatar": user.avatar_url,
            "room_id": str(room.id),
            "chat_url": reverse("chat_room_detail", args=[room.id]),
            "status_label": app.get_status_display(),
        },
    )

    return redirect('chat_room_detail', room_id=room.id)


def chat_room_view(request, room_id):
    """
    The 1-on-1 Private In-App Chat Room:
    - Privacy Shield: Phone numbers are masked until mutual contract signing
    - In-Chat Pre-Signed Contract Display
    - Worker 'Accept & Sign' button
    - When Signed: Phone numbers revealed with direct 1-click calling!
    """
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    room = get_object_or_404(
        ChatRoom.objects.select_related('job', 'employer', 'worker', 'application'),
        Q(employer=user) | Q(worker=user),
        id=room_id
    )

    # Check for existing contract attached to this chat
    contract = Contract.objects.filter(chat_room=room).first()
    messages_list = list(room.messages.select_related('sender').order_by('created_at'))

    # Distance between employer and worker
    dist_display = "Nearby"
    if room.employer.latitude and room.worker.latitude:
        d = calculate_haversine_distance(room.employer.latitude, room.employer.longitude, room.worker.latitude, room.worker.longitude)
        dist_display = format_distance(d)

    is_phone_unlocked = contract and contract.status == 'active'

    # Check for corresponding DigitalAgreement
    from .models import DigitalAgreement
    digital_agreement = DigitalAgreement.objects.filter(job=room.job).first()

    # Category-specific & context-aware suggestive questions for the Employer (Gemini Flash + Fallback)
    lang = request.session.get('lang', 'en')
    suggested_questions = []
    if user == room.employer:
        from .ai_service import generate_smart_employer_questions
        recent_msgs = [
            {"sender": m.sender.name, "text": m.message}
            for m in messages_list[-6:]
        ]
        suggested_questions = generate_smart_employer_questions(
            job_id=str(room.job.id),
            job_title=room.job.title,
            category=room.job.category,
            scope_of_work=room.job.responsibilities or room.job.title,
            duration_text=room.job.duration_text,
            offered_price=float(room.job.offered_price),
            recent_messages=recent_msgs,
            lang=lang,
            allow_remote_llm=False,  # Instant 0ms render; browser upgrades asynchronously via API
        )

    context = {
        'room': room,
        'job': room.job,
        'contract': contract,
        'digital_agreement': digital_agreement,
        'messages_list': messages_list,
        'current_user': user,
        'other_user': room.worker if user == room.employer else room.employer,
        'is_phone_unlocked': is_phone_unlocked,
        'dist_display': dist_display,
        'suggested_questions': suggested_questions,
    }
    return render(request, 'chat/room.html', context)


def chat_suggested_questions_api(request, room_id):
    """JSON endpoint returning updated context-aware questions as chat progresses."""
    user = _get_current_user(request)
    if not user:
        return JsonResponse({'questions': []}, status=401)
    room = get_object_or_404(ChatRoom.objects.select_related('job'), id=room_id, employer=user)
    lang = request.session.get('lang', 'en')
    recent_msgs = [
        {"sender": m.sender.name, "text": m.message}
        for m in room.messages.order_by('-created_at')[:6]
    ][::-1]
    from .ai_service import generate_smart_employer_questions
    questions = generate_smart_employer_questions(
        job_id=str(room.job.id),
        job_title=room.job.title,
        category=room.job.category,
        scope_of_work=room.job.responsibilities or room.job.title,
        duration_text=room.job.duration_text,
        offered_price=float(room.job.offered_price),
        recent_messages=recent_msgs,
        lang=lang,
    )
    return JsonResponse({'questions': questions})


def _get_employer_vetting_questions(category: str, lang: str = 'en'):
    """Returns simple, everyday, role-specific questions covering essential details without technical jargon."""
    en_bank = {
        'Driver': [
            "Do you have a valid driving licence, and have you driven in both city and highway traffic?",
            "Can you drive both manual (gear) and automatic cars?",
            "Will you be available for the full time needed without any rush?",
        ],
        'Electrician': [
            "Will you bring your own electrical tools and tester?",
            "Have you fixed main power board, inverter, or wiring issues before?",
            "Will you check the problem first and tell me before buying any new parts?",
        ],
        'Plumber': [
            "Will you bring your own plumbing tools and pipe wrench?",
            "Have you fixed wall pipe leaks and kitchen or bathroom taps before?",
            "After checking the leak, will you tell me what parts are needed before buying them?",
        ],
        'House Maid': [
            "Are you comfortable with all the work needed (sweeping, mopping, utensils, clothes)?",
            "Does this daily timing work well for you?",
            "Do you have any weekly off day preference we should decide before starting?",
        ],
        'Cook': [
            "Can you cook both veg and non-veg food (or pure veg, as needed)?",
            "How many people do you usually cook for, and what dishes are you best at?",
            "Does the morning and evening cooking time work for you?",
        ],
        'Carpenter': [
            "Will you bring your own carpentry tools (drill, saw, hammer)?",
            "Have you fixed kitchen cupboards, door locks, and hinges before?",
            "Once you see the work, can you tell me how much time it will take?",
        ],
        'Painter': [
            "Will you clean and prepare the wall properly before painting?",
            "Will you bring your own brushes, rollers, and covers to protect furniture?",
            "How many coats of paint and how much drying time will this work need?",
        ],
        'Gardener': [
            "Will you bring your own garden scissors and basic tools?",
            "Do you know how to take care of seasonal plants, grass, and plant insects?",
            "Which days and times work best for you for regular watering and care?",
        ],
        'Mechanic': [
            "Will you bring your own repair tools to check the vehicle here?",
            "Have you repaired this type of bike or car before?",
            "Will you tell me the parts cost before changing anything?",
        ],
        'Construction Worker': [
            "Have you done brick, plaster, or tile work like this before?",
            "Will you wear safety gloves and basic protection while working?",
            "Can you reach on time every day until the work finishes?",
        ],
    }
    hi_bank = {
        'Driver': [
            "क्या आपके पास पक्का ड्राइविंग लाइसेंस है और क्या आपने शहर और हाईवे दोनों जगह गाड़ी चलाई है?",
            "क्या आप गियर वाली और ऑटोमैटिक दोनों तरह की गाड़ियां चला लेते हैं?",
            "क्या आप पूरे तय समय तक बिना किसी जल्दबाजी के रुक पाएंगे?",
        ],
        'Electrician': [
            "क्या आप अपने बिजली के औजार और टेस्टर साथ लेकर आएंगे?",
            "क्या आपने पहले मेन बोर्ड, इनवर्टर और घर की वायरिंग का काम किया है?",
            "क्या आप पहले खराबी देखकर बता देंगे कि कौन सा नया सामान लाना होगा?",
        ],
        'Plumber': [
            "क्या आप अपने प्लंबिंग के औजार और पाना साथ लेकर आएंगे?",
            "क्या आपने पहले दीवार के अंदर के पाइप लीक और नल-टंकी का काम किया है?",
            "चेक करने के बाद क्या आप बता देंगे कि कौन सा सामान या फिटिंग खरीदनी है?",
        ],
        'House Maid': [
            "क्या आप झाड़ू-पोंछा, बर्तन और कपड़े धोने जैसे सभी काम आराम से कर लेंगी?",
            "क्या यह रोज़ का समय आपके आने-जाने के लिए सही है?",
            "क्या हफ्ते में छुट्टी को लेकर आपकी कोई खास बात है जो हम अभी तय कर लें?",
        ],
        'Cook': [
            "क्या आप शाकाहारी और मांसाहारी (या सिर्फ शाकाहारी, जैसी जरूरत हो) खाना बना लेते हैं?",
            "आपने आमतौर पर कितने लोगों का खाना बनाया है और कौन-सी चीज़ें सबसे अच्छी बनाते हैं?",
            "क्या सुबह और शाम के खाने का समय आपके लिए सही है?",
        ],
        'Carpenter': [
            "क्या आप अपने बढ़ई के औजार (ड्रिल, आरी, हथौड़ा) साथ लेकर आएंगे?",
            "क्या आपने पहले किचन की अलमारी, दरवाजे के लॉक और कब्जों का काम किया है?",
            "काम देखने के बाद क्या आप बता देंगे कि पूरा होने में कितना समय लगेगा?",
        ],
    }
    if lang == 'hi':
        return hi_bank.get(category, [
            "क्या आप इस काम के लिए जरूरी अपने औजार साथ लेकर आएंगे?",
            "क्या तय समय और पैसों पर आप काम शुरू करने के लिए तैयार हैं?",
            "क्या काम शुरू करने से पहले कुछ और पूछना या बताना है?",
        ])
    return en_bank.get(category, [
        "Will you bring your own tools needed for this work?",
        "Does the date, time, and payment work well for you?",
        "Is there anything else you want to ask or clarify before we finalize?",
    ])


@require_POST
def send_chat_message(request, room_id):
    """Appends an in-app message into the chat room and broadcasts via WebSocket."""
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    room = get_object_or_404(ChatRoom, Q(employer=user) | Q(worker=user), id=room_id)
    content = request.POST.get('message', '').strip()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if content:
        msg = ChatMessage.objects.create(
            chat_room=room,
            sender=user,
            message=content
        )
        # Real-Time WebSocket Broadcast to Recipient
        from django.urls import reverse
        from .realtime import broadcast_user_event
        recipient = room.worker if user == room.employer else room.employer
        local_ts = timezone.localtime(msg.created_at).strftime("%H:%M")
        broadcast_user_event(
            recipient.id,
            "chat_message_received",
            {
                "room_id": str(room.id),
                "message_id": str(msg.id),
                "sender_id": str(user.id),
                "sender_name": user.name,
                "sender_avatar": user.avatar_url,
                "message": content,
                "timestamp": local_ts,
                "chat_url": reverse("chat_room_detail", args=[room.id]),
            },
        )
        if is_ajax:
            return JsonResponse({
                "status": "ok",
                "sender_name": user.name,
                "message": content,
                "timestamp": local_ts,
            })

    if is_ajax:
        return JsonResponse({"status": "empty"}, status=400)
    return redirect('chat_room_detail', room_id=room.id)


def forward_presigned_contract(request, room_id):
    """
    Blueprint Section 05.B:
    Employer forwards the job's already-signed dynamic contract into the active chat room.
    Delivered directly into the chat feed for the worker to review.
    """
    auth_redirect = _require_auth(request, allowed_roles=['employer', 'admin'])
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    room = get_object_or_404(ChatRoom, id=room_id, application__job__employer=user)
    job = room.application.job

    # Attach or forward the DigitalAgreement to the chat room
    from .models import DigitalAgreement, AgreementAuditLog
    digital_agr = DigitalAgreement.objects.filter(job=job).first()
    if digital_agr:
        digital_agr.worker = room.application.worker
        digital_agr.status = 'WORKER_REVIEW_PENDING'
        digital_agr.save()

        AgreementAuditLog.objects.create(
            agreement=digital_agr,
            actor=user,
            event_type='FORWARDED_TO_WORKER',
            previous_status='PUBLISHED_AWAITING_WORKER',
            new_status='WORKER_REVIEW_PENDING',
            metadata={'chat_room_id': str(room.id), 'worker_id': str(room.application.worker.id)}
        )

    contract, created = Contract.objects.get_or_create(
        chat_room=room,
        job=job,
        employer=user,
        worker=room.application.worker,
        defaults={
            'contract_text': job.contract_terms,
            'agreed_price': job.offered_price,
            'duration_agreed': job.duration_text,
            'employer_signature': job.employer_signature,
            'employer_signed_at': job.employer_signed_at,
            'status': 'pending_worker_signature'
        }
    )

    # Post system message into chat
    ChatMessage.objects.create(
        chat_room=room,
        sender=user,
        message=f"[CONTRACT FORWARDED] Employer has sent the pre-signed contract (₹{job.offered_price:,.2f}). Please review and sign to unlock mutual contacts.",
        is_system_notice=True
    )

    room.application.status = 'contract_forwarded'
    room.application.save()

    # Real-Time WebSocket Broadcast to Worker
    from django.urls import reverse
    from .realtime import broadcast_user_event
    agr_url = reverse("agreement_worker_review", args=[digital_agr.id]) if digital_agr else reverse("chat_room_detail", args=[room.id])
    broadcast_user_event(
        room.application.worker.id,
        "contract_forwarded",
        {
            "application_id": str(room.application.id),
            "job_title": job.title,
            "employer_name": user.name,
            "employer_avatar": user.avatar_url,
            "agreement_url": agr_url,
            "chat_url": reverse("chat_room_detail", args=[room.id]),
        },
    )

    messages.success(request, "Pre-signed contract forwarded into the chat room.")
    return redirect('chat_room_detail', room_id=room.id)


def worker_sign_contract(request, contract_id):
    """
    Blueprint Section 05.B:
    Worker reviews and signs as 2nd Party -> UNLOCKS MUTUAL PHONE NUMBERS!
    Contract status becomes 'active' (Fully Executed).
    Privacy shield is lifted.
    """
    auth_redirect = _require_auth(request, allowed_roles=['worker'])
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    contract = get_object_or_404(Contract, id=contract_id, worker=user)

    # Apply 2nd-Party Digital Consent Signature
    timestamp = int(timezone.now().timestamp())
    contract.worker_signature = f"DIGITAL_SIGN_WRK_{user.id}_{timestamp}"
    contract.worker_signed_at = timezone.now()
    contract.status = 'active'  # FULLY EXECUTED!
    contract.save()

    # Update application state
    contract.chat_room.application.status = 'contract_accepted'
    contract.chat_room.application.save()

    # Post system announcement in chat
    ChatMessage.objects.create(
        chat_room=contract.chat_room,
        sender=user,
        message=f"🤝 CONTRACT FULLY EXECUTED! Both parties have signed. Mutual mobile numbers are now unlocked for direct voice coordination.",
        is_system_notice=True
    )

    messages.success(request, "🎉 Contract officially signed by both parties! Direct phone numbers are now unlocked.")
    return redirect('chat_room_detail', room_id=contract.chat_room.id)


# ==============================================================================
# Worker Profiles & Applications
# ==============================================================================

def workers_list_view(request):
    """Directory of nearby verified Karigars sorted by proximity."""
    user = _get_current_user(request)
    trade = request.GET.get('trade', 'all')

    user_lat = user.latitude if user and user.latitude else 28.6280
    user_lng = user.longitude if user and user.longitude else 77.3649

    workers = get_hyperlocal_workers(user_lat, user_lng, trade=trade, max_radius_km=10.0)
    categories = Category.objects.all().order_by('name_en')

    context = {
        'current_user': user,
        'workers': workers,
        'selected_trade': trade,
        'categories': categories,
    }
    return render(request, 'workers/list.html', context)


def worker_profile_view(request, worker_id=None):
    """Worker public or self profile page."""
    user = _get_current_user(request)

    if worker_id:
        worker_user = get_object_or_404(UserAccount, id=worker_id, role='worker')
        profile = get_object_or_404(WorkerProfile, user=worker_user)
    else:
        auth_redirect = _require_auth(request, allowed_roles=['worker'])
        if auth_redirect:
            return auth_redirect
        worker_user = user
        profile = user.worker_profile

    # Extract authentic location directly from coordinates if currently default 'Noida'
    if (profile.city == 'Noida' or not profile.city) and profile.latitude and profile.longitude:
        if abs(profile.latitude - 28.6280) > 0.05 or abs(profile.longitude - 77.3649) > 0.05:
            real_loc, real_city = reverse_geocode_coordinates(profile.latitude, profile.longitude)
            if real_city and real_city != 'India':
                profile.locality = real_loc
                profile.city = real_city
                profile.save(update_fields=['locality', 'city'])
                if worker_user.city != real_city:
                    worker_user.locality = real_loc
                    worker_user.city = real_city
                    worker_user.save(update_fields=['locality', 'city'])

    # Sanitize AI bio if legacy description had unverified claims
    if profile.ai_bio and ("2+ years" in profile.ai_bio or "years of practical" in profile.ai_bio):
        score_val = 2
        total_q = 2
        if profile.verification_badges and 'mcq_score' in profile.verification_badges:
            try:
                parts = str(profile.verification_badges['mcq_score']).split('/')
                score_val = int(parts[0])
                total_q = int(parts[1])
            except Exception:
                pass
        profile.ai_bio = generate_worker_ai_bio(
            name=worker_user.name,
            trades=profile.trades or [profile.primary_trade],
            score=score_val,
            total_mcqs=total_q
        )
        profile.save(update_fields=['ai_bio'])

    # Fetch applied jobs for the Applied Jobs tab
    applications = []
    if user and (user == worker_user):
        applications = Application.objects.filter(worker=user).select_related('job', 'job__employer', 'chat_room').order_by('-applied_at')

    # Party-specific, non-redundant worker statistics from real DB records
    total_applied = Application.objects.filter(worker=worker_user).count()
    active_chats_count = ChatRoom.objects.filter(worker=worker_user).count()
    signed_contracts_qs = Contract.objects.filter(worker=worker_user, status__in=['active', 'completed'])
    contracts_signed_count = signed_contracts_qs.count()
    total_contract_value = signed_contracts_qs.aggregate(total=Sum('agreed_price'))['total'] or 0
    mcq_score = (profile.verification_badges or {}).get('mcq_score', '100%')

    distance_display = f"{profile.city}"
    if user and user != worker_user and user.latitude and user.longitude and profile.latitude and profile.longitude:
        dist_km = calculate_haversine_distance(user.latitude, user.longitude, profile.latitude, profile.longitude)
        distance_display = format_distance(dist_km)

    worker_stats = {
        'total_applied': total_applied,
        'active_chats_count': active_chats_count,
        'contracts_signed_count': contracts_signed_count,
        'total_contract_value': total_contract_value,
        'mcq_score': mcq_score,
        'distance_display': distance_display,
    }

    # Specific, easy-to-read verified competency bullet points for employers & workers
    TRADE_BULLET_POINTS = {
        "Driver": [
            "Defensive driving techniques & situational road hazard prevention",
            "Pre-trip vehicle roadworthiness, tire & safety inspection checks",
            "Safe route navigation adhering to traffic & speed regulations",
        ],
        "Electrician": [
            "Domestic electrical wiring, load distribution & earth grounding",
            "Short-circuit diagnostics & 16A MCB overload troubleshooting",
            "Safe switchgear isolation preventing electrical current hazards",
        ],
        "Plumber": [
            "CPVC/PVC domestic pipeline layout installations & fixture fittings",
            "Teflon tape thread sealing & proactive leakage prevention",
            "Water pressure management and drainage pipe maintenance",
        ],
        "Cook": [
            "Strict hand sanitation and food hygiene preparation standards",
            "Separate cutting board protocols preventing cross-contamination",
            "Stovetop safety, temperature regulation, and clean workstation care",
        ],
        "House Maid": [
            "Surface-safe floor cleaning (avoiding acid damage on marble)",
            "Kitchen deep-degreasing utilizing safe, non-abrasive methods",
            "Organized domestic housekeeping and hygiene maintenance",
        ],
        "Carpenter": [
            "Plywood edge-banding tape application for moisture protection",
            "Precision pilot hole drilling preventing hardwood splitting",
            "Structural joinery, hardware fittings, and durable furniture repair",
        ],
        "Painter": [
            "Wall primer preparation, crack putty filling, and surface sanding",
            "Moisture sealing and weather-resistant coat application",
            "Even brush and roller finishing with clean edge cutting",
        ],
        "Gardener": [
            "Soil aeration, seasonal weeding, and organic fertilization",
            "Shrub and lawn pruning to stimulate healthy plant growth",
            "Efficient drip irrigation and domestic plant health upkeep",
        ],
        "Mechanic": [
            "Automotive engine and brake system preliminary diagnostics",
            "Fluid replacement protocols (engine oil, coolant, brake fluid)",
            "Electrical ignition inspection and mechanical maintenance",
        ],
        "Construction Worker": [
            "Structural masonry, precise mortar mixing ratios, and brick alignment",
            "Site safety protocol adherence including PPE compliance",
            "Scaffolding safety and heavy load material handling",
        ],
    }

    trade_points = []
    worker_trades = profile.trades or [profile.primary_trade] or ["Driver"]
    for tr in worker_trades:
        for cat_k, pts in TRADE_BULLET_POINTS.items():
            if cat_k.lower() in tr.lower() or tr.lower() in cat_k.lower():
                for p in pts:
                    if p not in trade_points and len(trade_points) < 4:
                        trade_points.append(p)
                break
    if not trade_points:
        trade_points = [
            "Verified practical trade safety protocols & equipment handling",
            "On-site diagnostic troubleshooting & quality execution",
            "Punctual task completion adhering to domestic property care"
        ]

    context = {
        'profile_user': worker_user,
        'profile': profile,
        'current_user': user,
        'is_self': (user == worker_user),
        'applications': applications,
        'trade_points': trade_points,
        'worker_stats': worker_stats,
    }
    return render(request, 'workers/profile.html', context)


def employer_profile_view(request, employer_id=None):
    """
    Dedicated Employer Profile Showcase:
    - Typographic dynamic watermark (Google Font Boldonse)
    - Employer identity details, DigiLocker verified status, location
    - In-situ profile photo crop & edit with WebP conversion
    - P2P Phone privacy shield (visible/editable to self, masked to third parties)
    - Posted Gigs / Active Jobs list
    """
    current_user = _get_current_user(request)
    
    if employer_id:
        try:
            employer_user = UserAccount.objects.get(id=employer_id, role='employer')
        except UserAccount.DoesNotExist:
            messages.error(request, "Employer profile not found.")
            return redirect('home')
    else:
        auth_redirect = _require_auth(request, allowed_roles=['employer', 'admin'])
        if auth_redirect:
            return auth_redirect
        employer_user = current_user

    is_self = (current_user == employer_user)

    # Clean raw GPS coordinate string from locality or city if needed
    cleaned_locality = employer_user.locality or ''
    cleaned_city = employer_user.city or ''
    if 'GPS (' in cleaned_locality or '°' in cleaned_locality:
        cleaned_locality = 'Local Area'
    if 'GPS (' in cleaned_city or '°' in cleaned_city:
        cleaned_city = 'Punjab' if '75.' in cleaned_city else 'India'

    # Get employer's posted jobs with prefetched digital agreements
    jobs = Job.objects.filter(employer=employer_user).prefetch_related('digital_agreements').annotate(
        applicant_count=Count('applications')
    ).order_by('-created_at')

    # Identify any unfinished draft job
    db_draft = Job.objects.filter(employer=employer_user, status='draft', is_active=False).order_by('-created_at').first()

    # Contracts stats
    active_contracts_count = Contract.objects.filter(job__employer=employer_user, status='active').count()
    completed_contracts_count = Contract.objects.filter(job__employer=employer_user, status='completed').count()

    context = {
        'employer_user': employer_user,
        'cleaned_locality': cleaned_locality,
        'cleaned_city': cleaned_city,
        'current_user': current_user,
        'is_self': is_self,
        'jobs': jobs,
        'db_draft': db_draft,
        'total_jobs_count': jobs.count(),
        'active_contracts_count': active_contracts_count,
        'completed_contracts_count': completed_contracts_count,
    }
    return render(request, 'employers/profile.html', context)


@require_POST
def update_worker_photo_view(request):
    """AJAX endpoint to update profile photo directly from profile page."""
    user = _get_current_user(request)
    if not user:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
            photo_data = data.get('profile_picture', '').strip()
        else:
            photo_data = request.POST.get('profile_picture', '').strip()

        if photo_data:
            user.profile_picture = ensure_webp_data_url(photo_data)
            user.save(update_fields=['profile_picture'])
            return JsonResponse({'status': 'success', 'avatar_url': user.avatar_url})
        return JsonResponse({'status': 'error', 'message': 'No image data provided'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_POST
def update_user_phone_view(request):
    """AJAX endpoint to update user's registered phone number and sync database."""
    user = _get_current_user(request)
    if not user:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
            new_phone = data.get('phone', '').strip().replace(' ', '').replace('-', '')
        else:
            new_phone = request.POST.get('phone', '').strip().replace(' ', '').replace('-', '')

        if not re.search(r'^[6-9]\d{9}$', new_phone):
            return JsonResponse({'status': 'error', 'message': 'Please enter a valid 10-digit Indian mobile number.'}, status=400)

        # Check if already registered by someone else
        if UserAccount.objects.filter(phone=new_phone).exclude(id=user.id).exists():
            return JsonResponse({'status': 'error', 'message': 'An account with this phone number already exists.'}, status=400)

        user.phone = new_phone
        user.save(update_fields=['phone'])

        # Keep worker profile in sync if applicable
        if hasattr(user, 'worker_profile') and user.worker_profile:
            wp = user.worker_profile
            wp.karigar_id = f"RS-IND-{new_phone[-4:]}"
            if wp.verification_badges and 'digilocker_token' in wp.verification_badges:
                wp.verification_badges['digilocker_token'] = f"DL-AADH-2026-{new_phone[-4:]}"
            wp.save(update_fields=['karigar_id', 'verification_badges'])

        return JsonResponse({
            'status': 'success',
            'phone': new_phone,
            'message': 'Phone number updated successfully.'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def my_applications_view(request):
    """Worker's applied jobs and active contracts."""
    auth_redirect = _require_auth(request, allowed_roles=['worker'])
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    applications = Application.objects.filter(worker=user).select_related('job', 'job__employer', 'chat_room').order_by('-applied_at')

    context = {
        'current_user': user,
        'applications': applications,
    }
    return render(request, 'workers/my_applications.html', context)


# ==============================================================================
# DigiLocker Trust Rails & Platform Analytics
# ==============================================================================

def digilocker_verify_view(request):
    """Simulated DigiLocker OAuth sandbox verifying worker's Aadhaar / DL."""
    auth_redirect = _require_auth(request)
    if auth_redirect:
        return auth_redirect

    user = _get_current_user(request)
    user.is_aadhaar_verified = True
    user.save()

    if hasattr(user, 'worker_profile'):
        profile = user.worker_profile
        badges = profile.verification_badges or {}
        badges['aadhaar_verified'] = True
        profile.verification_badges = badges
        profile.save()

    messages.success(request, "✓ DigiLocker Aadhaar Verification Successful! 'Aadhaar Verified' badge awarded.")
    if user.role == 'worker':
        return redirect('worker_profile')
    return redirect('home')


def analytics_dashboard_view(request):
    """Platform metrics: zero brokerage savings, contract counts, trade distribution."""
    user = _get_current_user(request)
    
    total_workers = WorkerProfile.objects.count()
    total_employers = UserAccount.objects.filter(role='employer').count()
    total_jobs = Job.objects.count()
    total_contracts = Contract.objects.filter(status='active').count()
    total_savings = total_contracts * 18000  # ₹18,000 avg brokerage saved

    trade_stats = Job.objects.values('category').annotate(count=Count('category')).order_by('-count')[:5]

    context = {
        'current_user': user,
        'total_workers': total_workers,
        'total_employers': total_employers,
        'total_jobs': total_jobs,
        'total_contracts': total_contracts,
        'total_savings': total_savings,
        'trade_stats': trade_stats,
    }
    return render(request, 'analytics/dashboard.html', context)
