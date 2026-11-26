"""
Context processors for Rojgar Setu:
- Bilingual English/Hindi dictionary for P2P zero-brokerage hiring
- User session state & active user object
- PostgreSQL / Supabase database status diagnostic badge
"""

from django.conf import settings
from .models import UserAccount, Job

TRANSLATIONS = {
    'en': {
        'brand_title': 'Rojgar Setu',
        'brand_tagline': 'Direct Hiring • Zero Agency Brokerage',
        'nav_home': 'Home',
        'nav_jobs': 'Find Jobs',
        'nav_workers': 'Find Workers',
        'nav_post_job': 'Post a Job',
        'nav_my_jobs': 'My Jobs',
        'nav_my_apps': 'My Applications',
        'nav_profile': 'Profile',
        'nav_analytics': 'Analytics',
        'nav_login': 'Login',
        'nav_register': 'Register',
        'nav_logout': 'Logout',
        'role_worker': 'Worker',
        'role_employer': 'Employer',
        'apply_now': '1-Click Apply',
        'applied': 'Applied ✓',
        'view_details': 'View Contract Terms',
        'chat_now': 'In-App Chat',
        'presigned_badge': 'Agreement Attached ✓',
        'phone_unlocked': 'Phone Unlocked 📞',
        'phone_masked': 'Privacy Shield: Phone Masked 🔒',
        'lang_toggle': 'हिंदी में देखें',
        'current_lang': 'en',
    },
    'hi': {
        'brand_title': 'रोजगार सेतु',
        'brand_tagline': 'प्रत्यक्ष व्यक्तिगत रोजगार • शून्य दलाली व बिचौलिया',
        'nav_home': 'होम',
        'nav_jobs': 'काम खोजें',
        'nav_workers': 'कारीगर खोजें',
        'nav_post_job': 'काम पोस्ट करें',
        'nav_my_jobs': 'मेरे काम',
        'nav_my_apps': 'मेरे आवेदन',
        'nav_profile': 'प्रोफाइल',
        'nav_analytics': 'डैशबोर्ड',
        'nav_login': 'लॉगिन',
        'nav_register': 'नया खाता',
        'nav_logout': 'लॉगआउट',
        'role_worker': 'कारीगर',
        'role_employer': 'नियोक्ता',
        'apply_now': '1-क्लिक आवेदन',
        'applied': 'आवेदन किया जा चुका है ✓',
        'view_details': 'अनुबंध की शर्तें देखें',
        'chat_now': 'ऐप चैट खोलें',
        'presigned_badge': 'पूर्व-हस्ताक्षरित अनुबंध संलग्न ✓',
        'phone_unlocked': 'फोन नंबर अनलॉक 📞',
        'phone_masked': 'गोपनीयता शील्ड: फोन सुरक्षित 🔒',
        'lang_toggle': 'Switch to English',
        'current_lang': 'hi',
    }
}


def language_and_user_context(request):
    """Inject language dictionary, session user, and DB status into all templates."""
    lang = request.GET.get('lang')
    if lang in ('en', 'hi'):
        request.session['lang'] = lang
    else:
        lang = request.session.get('lang', 'hi')  # Default to Hindi for inclusive blue-collar UX

    t_dict = TRANSLATIONS.get(lang, TRANSLATIONS['hi'])

    user_id = request.session.get('rojgar_user_id')
    current_user = getattr(request, '_rojgar_cached_user', None)
    employer_draft_count = 0
    if user_id and current_user is None:
        try:
            current_user = UserAccount.objects.get(id=user_id)
            request._rojgar_cached_user = current_user
        except UserAccount.DoesNotExist:
            pass
    if current_user and current_user.role == 'employer':
        employer_draft_count = Job.objects.filter(
            employer=current_user,
            status='draft',
            is_active=False
        ).count()

    # Supabase connection indicator
    db_engine = settings.DATABASES['default'].get('ENGINE', '')
    is_postgres = 'postgresql' in db_engine

    db_status = {
        'mode': 'Supabase PostgreSQL 17 + PostGIS' if is_postgres else 'Local SQLite (Demo)',
        'is_postgres': is_postgres,
        'db_name': settings.DATABASES['default'].get('NAME', 'postgres'),
    }

    return {
        'T': t_dict,
        'current_lang': lang,
        'current_user': current_user,
        'employer_draft_count': employer_draft_count,
        'db_status': db_status,
    }
