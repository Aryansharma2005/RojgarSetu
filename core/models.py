"""
Master Database Models for Rojgar Setu (रोजगार सेतु).
Master Full-Stack Engineering Specification Version 5.5 • P2P Architecture
Dual-Actor Hyperlocal Platform for Direct Individual Hiring • Zero Agency Brokerage
PostgreSQL 16+ & PostGIS GiST Integration
"""

import uuid
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone


class UserAccount(models.Model):
    """
    Core User entity representing strictly Individual actors:
    - Worker: Blue-collar job seeker / Karigar
    - Employer: Individual homeowner / Hirer
    (Zero agencies, contractors, or corporate profiles permitted)
    """
    ROLE_CHOICES = [
        ('worker', 'Individual Worker / Karigar (कारीगर)'),
        ('employer', 'Individual Homeowner / Hirer (गृहस्वामी / नियोक्ता)'),
        ('admin', 'Administrator'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=15, unique=True, db_index=True)
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    password_hash = models.CharField(max_length=255)
    preferred_lang = models.CharField(max_length=5, default='hi', choices=[('hi', 'Hindi'), ('en', 'English')])
    
    # Trust & Verification Flags
    is_phone_verified = models.BooleanField(default=True)
    is_aadhaar_verified = models.BooleanField(default=False)
    
    # Profile Picture (Base64 cropped data URL or image path)
    profile_picture = models.TextField(blank=True, null=True, default='')
    
    # Exact Geolocation Coordinates (WGS-84 Point)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    city = models.CharField(max_length=80, blank=True, default='Noida')
    locality = models.CharField(max_length=120, blank=True, default='')
    pincode = models.CharField(max_length=10, blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    @property
    def masked_phone(self):
        """Masks phone number for pre-contract privacy rails: e.g. +91 98XXX-XX111"""
        p = str(self.phone).strip()
        if len(p) >= 10:
            return f"+91 {p[:2]}XXX-XX{p[-3:]}"
        return f"+91 {p[:2]}***{p[-2:]}" if len(p) > 4 else p

    @property
    def masked_email(self):
        """Masks email: e.g. a***@domain.com"""
        if not self.email:
            return "Not Provided"
        parts = self.email.split('@')
        if len(parts) == 2:
            return f"{parts[0][0]}***@{parts[1]}"
        return "Protected"

    @property
    def avatar_url(self):
        """Returns uploaded profile picture data URL or dynamic clean initials fallback."""
        if self.profile_picture:
            return self.profile_picture
        clean_name = self.name.replace(' ', '+') if self.name else 'User'
        return f"https://ui-avatars.com/api/?name={clean_name}&background=0a0a0a&color=fff&size=256&bold=true"

    def __str__(self):
        return f"{self.name} ({self.get_role_display()} - {self.phone})"


class Category(models.Model):
    """Vocational trade categories (e.g., Plumber, House Maid, Cook, Electrician)."""
    name_en = models.CharField(max_length=80, unique=True)
    name_hi = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80, unique=True)
    icon = models.CharField(max_length=50, default='wrench')
    description = models.TextField(blank=True)
    typical_wage_daily = models.IntegerField(default=600)
    sub_services = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return f"{self.name_en} / {self.name_hi}"


class WorkerProfile(models.Model):
    """
    Unified Karigar Profile.
    Supports Multi-Trade Selection (1 to 4 categories) with Gemini Flash AI assessment scoring.
    """
    WAGE_BASIS_CHOICES = [
        ('daily', 'Per Day (दैनिक)'),
        ('monthly', 'Per Month (मासिक)'),
        ('per_job', 'Per Task (प्रति कार्य)'),
        ('hourly', 'Hourly (प्रति घंटा)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='worker_profile')
    karigar_id = models.CharField(max_length=30, unique=True, db_index=True)
    
    # Multi-Trade Selection (1 to 4 trades)
    trades = models.JSONField(default=list)
    primary_trade = models.CharField(max_length=80, blank=True)
    skills = models.JSONField(default=dict, blank=True)
    
    experience_years = models.IntegerField(default=1)
    wage_type = models.CharField(max_length=20, default='daily', choices=WAGE_BASIS_CHOICES)
    expected_wage = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    is_available = models.BooleanField(default=True)
    
    # Geolocation Coordinates
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    city = models.CharField(max_length=80, blank=True, default='Noida')
    locality = models.CharField(max_length=120, blank=True, default='')
    pincode = models.CharField(max_length=10, blank=True, default='')
    
    # AI Verification Badges JSON:
    # {"aadhaar_verified": True, "mcq_passed": True, "mcq_score": "5/5", "skill_badge": "Skills Tested ★"}
    verification_badges = models.JSONField(default=dict, blank=True)
    ai_bio = models.TextField(blank=True)
    
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    total_reviews = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def avatar_url(self):
        return self.user.avatar_url

    def __str__(self):
        return f"{self.karigar_id} - {self.user.name} ({self.primary_trade})"


class Job(models.Model):
    """
    P2P Job Opening created by an Individual Homeowner.
    Includes the 1st-Party Pre-Signed Dynamic Contract attached at creation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employer = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=80, db_index=True)
    responsibilities = models.TextField()
    duration_text = models.CharField(max_length=100, default='1 Day')
    offered_price = models.DecimalField(max_digits=10, decimal_places=2)
    wage_period = models.CharField(max_length=20, default='per_job')
    
    # Exact Work Location
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    city = models.CharField(max_length=80, default='Noida')
    locality = models.CharField(max_length=120, blank=True, default='')
    pincode = models.CharField(max_length=10, blank=True, default='')
    
    # Dynamic Pre-Signed Contract & 1st-Party Signature
    contract_terms = models.TextField()
    employer_signature = models.CharField(max_length=255)
    employer_signed_at = models.DateTimeField(default=timezone.now)
    
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, default='active')  # 'active', 'filled', 'closed'
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.category}) - ₹{self.offered_price}"

    @property
    def latest_agreement(self):
        """Returns the most recent digital agreement synthesized for this job."""
        return self.digital_agreements.order_by('-created_at').first()

    def get_wage_period_display(self):
        """Returns human-readable wage basis label."""
        mapping = {
            'per_job': 'Per Task',
            'daily': 'Per Day',
            'monthly': 'Per Month',
        }
        return mapping.get(self.wage_period, self.wage_period.replace('_', ' ').title())


class Application(models.Model):
    """Worker's 1-Click Application to a Hyperlocal Job."""
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('chat_initiated', 'Chat Initiated'),
        ('contract_forwarded', 'Agreement Sent'),
        ('contract_accepted', 'Contract Accepted'),
        ('rejected', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    worker = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='applications')
    fit_score = models.FloatField(default=100.0)  # AI test score percentage
    status = models.CharField(max_length=30, default='applied', choices=STATUS_CHOICES)
    notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['job', 'worker'], name='unique_job_worker_application')
        ]

    def __str__(self):
        return f"App by {self.worker.name} for {self.job.title} [{self.status}]"


class ChatRoom(models.Model):
    """
    1-on-1 Secure Private Chat between Homeowner & Worker.
    Phone numbers & emails remain masked until mutual contract signing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='chat_room')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='chat_rooms')
    employer = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='employer_chat_rooms')
    worker = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='worker_chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat: {self.employer.name} <-> {self.worker.name} ({self.job.category})"


class ChatMessage(models.Model):
    """In-app messages exchanged inside the masked chat room."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    message = models.TextField()
    is_system_notice = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Msg from {self.sender.name}: {self.message[:30]}"


class Contract(models.Model):
    """
    The Dynamic Pre-Signed P2P Contract.
    Inherited from Job Creation with 1st-Party Signature.
    When Worker adds 2nd-Party Signature, status becomes 'active', instantly revealing telephone numbers!
    """
    STATUS_CHOICES = [
        ('pending_worker_signature', 'Pending Worker Signature (हस्ताक्षर प्रतीक्षित)'),
        ('active', 'Active / Fully Executed (अनुबंध पूर्ण - फोन नंबर अनलॉक)'),
        ('completed', 'Work Completed (कार्य संपन्न)'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_room = models.OneToOneField(ChatRoom, on_delete=models.CASCADE, related_name='contract')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='contracts')
    employer = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='contracts_as_employer')
    worker = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='contracts_as_worker')
    
    # Contract Terms & Compensation
    contract_text = models.TextField()
    agreed_price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_agreed = models.CharField(max_length=100)
    
    # 1st-Party Signature (From Employer at Job Creation)
    employer_signature = models.CharField(max_length=255)
    employer_signed_at = models.DateTimeField(default=timezone.now)
    
    # 2nd-Party Signature (From Worker inside Chat)
    worker_signature = models.CharField(max_length=255, null=True, blank=True)
    worker_signed_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=35, default='pending_worker_signature', choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_fully_executed(self):
        return self.status == 'active' and bool(self.worker_signature)

    def __str__(self):
        return f"Contract #{str(self.id)[:8]} - {self.job.title} [{self.status}]"


# ==============================================================================
# Master Digital Work Agreement & E-Signature Architecture
# ==============================================================================

class AgreementTemplate(models.Model):
    """
    Central Legal Template and Clause Registry.
    Stores lawyer-reviewed master contractual terms and category-specific addendums.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=80, db_index=True)  # Electrician, Plumber, House Maid, Cook, Carpenter, Painter, Gardener, Driver, General
    template_name = models.CharField(max_length=150)
    template_version = models.CharField(max_length=20, default='v1.0')
    is_active = models.BooleanField(default=True)
    
    # Clause definitions stored as structured JSON
    master_clauses = models.JSONField(default=list, help_text="Common master contract clauses for P2P hiring")
    category_specific_clauses = models.JSONField(default=list, help_text="Occupation-specific statutory and safety clauses")
    
    approval_status = models.CharField(max_length=20, default='approved')  # draft, approved, deprecated
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', '-created_at']

    def __str__(self):
        return f"{self.category} Agreement Template ({self.template_version})"


class DigitalAgreement(models.Model):
    """
    Complete Digital Work Agreement & E-Signature Legal Entity.
    Manages the full lifecycle across Employer creation -> Employer signing -> Worker matching -> Worker signing -> Execution.
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft (प्रारूप)'),
        ('EMPLOYER_REVIEW_PENDING', 'Awaiting Employer Review (समीक्षा प्रतीक्षित)'),
        ('EMPLOYER_SIGNED', 'Employer Signed / Published (नियोक्ता द्वारा हस्ताक्षरित)'),
        ('PUBLISHED_AWAITING_WORKER', 'Published & Awaiting Worker (कारीगर प्रतीक्षित)'),
        ('WORKER_REVIEW_PENDING', 'Worker Reviewing (कारीगर समीक्षाधीन)'),
        ('FULLY_EXECUTED', 'Fully Executed & Legally Binding (अनुबंध पूर्ण व प्रभावी)'),
        ('DECLINED_BY_WORKER', 'Declined by Worker (कारीगर द्वारा अस्वीकृत)'),
        ('EXPIRED', 'Expired (समय समाप्त)'),
        ('CANCELLED', 'Cancelled (रद्द किया गया)'),
        ('AMENDMENT_PENDING', 'Amendment Pending (संशोधन विचाराधीन)'),
        ('DISPUTED', 'Disputed (विवादित)'),
        ('TERMINATED', 'Terminated (समाप्त)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agreement_number = models.CharField(max_length=50, unique=True, db_index=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='digital_agreements')
    employer = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='employer_agreements')
    worker = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='worker_agreements')
    category = models.CharField(max_length=80, db_index=True)
    
    template = models.ForeignKey(AgreementTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    template_version = models.CharField(max_length=20, default='v1.0')
    agreement_version = models.PositiveIntegerField(default=1)
    
    status = models.CharField(max_length=35, default='DRAFT', choices=STATUS_CHOICES, db_index=True)
    
    # Job snapshot data at generation
    job_data_snapshot = models.JSONField(default=dict)
    
    # Full compiled legal agreement document (HTML for PDF reader & canonical plain text for hashing)
    compiled_agreement_html = models.TextField()
    compiled_agreement_text = models.TextField()
    
    # SHA-256 Document Hash (ensures document immutability upon signing)
    document_hash = models.CharField(max_length=64, blank=True, db_index=True)
    
    # Employer signature & declaration
    employer_signature_data = models.TextField(blank=True, help_text="Base64 encoded PNG drawn signature")
    employer_signed_at = models.DateTimeField(null=True, blank=True)
    employer_declaration_affirmed = models.BooleanField(default=False)
    employer_auth_method = models.CharField(max_length=50, default='SESSION_AUTH')
    
    # Worker signature & declaration
    worker_signature_data = models.TextField(blank=True, help_text="Base64 encoded PNG drawn signature")
    worker_signed_at = models.DateTimeField(null=True, blank=True)
    worker_declaration_affirmed = models.BooleanField(default=False)
    worker_auth_method = models.CharField(max_length=50, default='SESSION_AUTH')
    
    # Fully Executed metadata & generated PDF file path
    fully_executed_at = models.DateTimeField(null=True, blank=True)
    generated_pdf_file = models.CharField(max_length=300, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.agreement_number} [{self.get_status_display()}] - {self.job.title}"


class AgreementSignature(models.Model):
    """
    Immutable Signature Audit Record.
    Captures exact timestamp, document SHA-256 hash, and signer metadata.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agreement = models.ForeignKey(DigitalAgreement, on_delete=models.CASCADE, related_name='signatures')
    signer = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    role = models.CharField(max_length=20)  # 'employer' or 'worker'
    
    signature_data = models.TextField(help_text="Base64 PNG signature stream")
    document_hash_at_signing = models.CharField(max_length=64)
    document_version = models.PositiveIntegerField(default=1)
    
    signed_at = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    declaration_text = models.TextField()

    def __str__(self):
        return f"Sig by {self.signer.name} ({self.role}) on {self.agreement.agreement_number}"


class AgreementAuditLog(models.Model):
    """
    Complete Verifiable Audit Trail for Agreement Lifecycle Events.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agreement = models.ForeignKey(DigitalAgreement, on_delete=models.CASCADE, related_name='audit_logs')
    actor = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=50, db_index=True)  # CREATED, EMPLOYER_SIGNED, WORKER_VIEWED, WORKER_SIGNED, DECLINED, PDF_GENERATED, DISPUTE_RAISED
    
    previous_status = models.CharField(max_length=35, blank=True)
    new_status = models.CharField(max_length=35, blank=True)
    document_version = models.PositiveIntegerField(default=1)
    
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.event_type} on {self.agreement.agreement_number} at {self.timestamp}"


class AgreementDispute(models.Model):
    """
    Dispute and Incident Management Foundation for Executed Agreements.
    """
    CATEGORY_CHOICES = [
        ('PAYMENT', 'Payment Settlement Dispute (भुगतान विवाद)'),
        ('WORK_QUALITY', 'Work Quality & Incomplete Deliverables (गुणवत्ता विवाद)'),
        ('PROPERTY_DAMAGE', 'Property Damage or Loss (संपत्ति क्षति)'),
        ('SAFETY', 'Safety Incident or Breach (सुरक्षा उल्लंघन)'),
        ('UNAUTHORIZED_CANCELLATION', 'Unilateral Contract Breach (अनुबंध उल्लंघन)'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Open (खुला है)'),
        ('UNDER_REVIEW', 'Under Platform Facilitation (समीक्षाधीन)'),
        ('RESOLVED', 'Resolved Mutually (सुलझा हुआ)'),
        ('ESCALATED', 'Escalated to External Authority (प्राधिकरण को संदर्भित)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agreement = models.ForeignKey(DigitalAgreement, on_delete=models.CASCADE, related_name='disputes')
    raised_by = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='raised_disputes')
    
    dispute_category = models.CharField(max_length=40, choices=CATEGORY_CHOICES)
    description = models.TextField()
    incident_date = models.DateField(null=True, blank=True)
    evidence_urls = models.JSONField(default=list, help_text="Uploaded photos, receipts or chat transcripts")
    
    status = models.CharField(max_length=25, default='OPEN', choices=STATUS_CHOICES, db_index=True)
    other_party_response = models.TextField(blank=True)
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Dispute on {self.agreement.agreement_number} [{self.get_status_display()}]"
