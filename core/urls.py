"""
URL patterns for Rojgar Setu (Master Full-Stack P2P Architecture v5.5).
"""

from django.urls import path
from . import views
from . import agreement_views
from . import superadmin_views

urlpatterns = [
    # Landing & Discovery
    path('', views.home_view, name='home'),
    
    # Dual-Actor Registration & Auth
    path('register/', views.register_view, name='register'),
    path('register/worker/', views.register_worker_view, name='register_worker'),
    path('register/employer/', views.register_employer_view, name='register_employer'),
    path('api/check-registration/', views.check_registration_availability_api, name='check_registration_availability'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dynamic AI Skill Assessment (Gemini Flash)
    path('assessment/', views.ai_assessment_view, name='ai_assessment'),
    
    # Hyperlocal Job Rail & Pre-Signed Contracts
    path('jobs/', views.jobs_list_view, name='jobs_list'),
    path('jobs/post/', views.job_create_view, name='job_create'),
    path('jobs/<uuid:job_id>/', views.job_detail_view, name='job_detail'),
    path('jobs/<uuid:job_id>/delete-draft/', views.job_delete_draft_view, name='job_delete_draft'),
    path('jobs/<uuid:job_id>/toggle-status/', views.job_toggle_status_view, name='job_toggle_status'),
    path('jobs/<uuid:job_id>/apply/', views.apply_job_view, name='apply_job'),
    path('jobs/<uuid:job_id>/applicants/', views.job_applicants_view, name='job_applicants'),
    path('my-jobs/', views.my_jobs_view, name='my_jobs'),
    
    # Master Digital Work Agreement & E-Signature Rail
    path('agreements/', agreement_views.agreements_dashboard_view, name='agreements_dashboard'),
    path('agreements/<uuid:agreement_id>/employer-review/', agreement_views.agreement_employer_review_view, name='agreement_employer_review'),
    path('agreements/<uuid:agreement_id>/worker-review/', agreement_views.agreement_worker_review_view, name='agreement_worker_review'),
    path('agreements/<uuid:agreement_id>/decline/', agreement_views.agreement_decline_view, name='agreement_decline'),
    path('agreements/<uuid:agreement_id>/download/', agreement_views.agreement_download_pdf_view, name='agreement_download_pdf'),
    path('agreements/<uuid:agreement_id>/dispute/', agreement_views.agreement_raise_dispute_view, name='agreement_raise_dispute'),
    path('api/agreements/<uuid:agreement_id>/history/', agreement_views.agreement_audit_history_api, name='agreement_audit_history_api'),

    # 5-Stage In-App Chat & Contract Handshake Pipeline
    path('applications/<uuid:app_id>/chat/', views.initiate_chat_view, name='initiate_chat'),
    path('chat/<uuid:room_id>/', views.chat_room_view, name='chat_room_detail'),
    path('chat/<uuid:room_id>/send/', views.send_chat_message, name='send_chat_message'),
    path('chat/<uuid:room_id>/suggested-questions/', views.chat_suggested_questions_api, name='chat_suggested_questions_api'),
    path('chat/<uuid:room_id>/forward-contract/', views.forward_presigned_contract, name='forward_presigned_contract'),
    path('contract/<uuid:contract_id>/sign/', views.worker_sign_contract, name='worker_sign_contract'),
    
    # Karigar Directory & Profiles
    path('workers/', views.workers_list_view, name='workers_list'),
    path('worker/profile/', views.worker_profile_view, name='worker_profile'),
    path('worker/profile/<uuid:worker_id>/', views.worker_profile_view, name='worker_profile_detail'),
    path('worker/applications/', views.my_applications_view, name='my_applications'),
    path('worker/update-photo/', views.update_worker_photo_view, name='update_worker_photo'),
    path('user/update-phone/', views.update_user_phone_view, name='update_user_phone'),
    
    # Employer Profiles
    path('employer/profile/', views.employer_profile_view, name='employer_profile'),
    path('employer/profile/<uuid:employer_id>/', views.employer_profile_view, name='employer_profile_detail'),
    
    # Trust Rails & Platform Analytics
    path('verify/digilocker/', views.digilocker_verify_view, name='digilocker_verify'),

    # SuperAdmin Control Center
    path('superadmin/login/', superadmin_views.superadmin_login_view, name='superadmin_login'),
    path('superadmin/', superadmin_views.superadmin_dashboard_view, name='superadmin_dashboard'),
    path('superadmin/users/<uuid:user_id>/edit/', superadmin_views.superadmin_user_edit_view, name='superadmin_user_edit'),
    path('superadmin/users/<uuid:user_id>/delete/', superadmin_views.superadmin_user_delete_view, name='superadmin_user_delete'),
    path('superadmin/jobs/<uuid:job_id>/action/', superadmin_views.superadmin_job_action_view, name='superadmin_job_action'),
    path('superadmin/disputes/<uuid:dispute_id>/update/', superadmin_views.superadmin_dispute_update_view, name='superadmin_dispute_update'),
    path('analytics/', views.analytics_dashboard_view, name='analytics'),
]
