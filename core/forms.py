"""
Form classes and validation for Rojgar Setu (P2P Architecture).
Enforces:
- 1-to-4 trade selection for workers
- HTML5 GPS coordinates capture
- 10-digit Indian mobile validation
- Employer 1st-party digital signature on job creation
"""

import re
from django import forms
from .models import UserAccount, Job, WorkerProfile, Category


class WorkerRegisterForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full Name'})
    )
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '10-digit Mobile (e.g. 9876543210)'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email (Optional)'})
    )
    password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Password (min 6 chars)'})
    )
    
    # Selected trades (1 to 4)
    trades = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'trade-checkbox'}),
        help_text='Select between 1 and 4 vocational trades'
    )
    
    experience_years = forms.IntegerField(
        min_value=0, max_value=40, initial=2,
        widget=forms.NumberInput(attrs={'class': 'form-input'})
    )
    expected_wage = forms.DecimalField(
        min_value=100, initial=500,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 600'})
    )
    wage_type = forms.ChoiceField(
        choices=[('daily', 'Per Day'), ('monthly', 'Per Month'), ('per_job', 'Per Task')],
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    
    # Geolocation fields
    latitude = forms.FloatField(required=False, widget=forms.HiddenInput())
    longitude = forms.FloatField(required=False, widget=forms.HiddenInput())
    city = forms.CharField(max_length=80, initial='Noida', widget=forms.TextInput(attrs={'class': 'form-input'}))
    locality = forms.CharField(max_length=120, required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Colony / Sector / Area'}))

    def __init__(self, *args, lang='hi', **kwargs):
        super().__init__(*args, **kwargs)
        if lang == 'hi':
            self.fields['name'].widget.attrs['placeholder'] = 'पूरा नाम'
            self.fields['phone'].widget.attrs['placeholder'] = '10-अंकों का मोबाइल (जैसे 9876543210)'
            self.fields['email'].widget.attrs['placeholder'] = 'ईमेल (वैकल्पिक)'
            self.fields['password'].widget.attrs['placeholder'] = 'पासवर्ड (कम से कम 6 अक्षर)'
            self.fields['locality'].widget.attrs['placeholder'] = 'कॉलोनी / सेक्टर / क्षेत्र'
            self.fields['wage_type'].choices = [
                ('daily', 'दैनिक (प्रति दिन)'),
                ('monthly', 'मासिक (प्रति माह)'),
                ('per_job', 'प्रति कार्य')
            ]
            self.fields['trades'].choices = [
                ('Electrician', 'इलेक्ट्रीशियन'),
                ('Plumber', 'प्लंबर'),
                ('House Maid', 'घरेलू सहायिका'),
                ('Cook', 'रसोइया'),
                ('Carpenter', 'बढ़ई'),
                ('Painter', 'पेंटर'),
                ('Gardener', 'माली'),
                ('Driver', 'चालक'),
                ('Mechanic', 'मैकेनिक'),
                ('Construction Worker', 'निर्माण श्रमिक'),
            ]
        else:
            self.fields['name'].widget.attrs['placeholder'] = 'Full Name'
            self.fields['phone'].widget.attrs['placeholder'] = '10-digit Mobile (e.g. 9876543210)'
            self.fields['email'].widget.attrs['placeholder'] = 'Email (Optional)'
            self.fields['password'].widget.attrs['placeholder'] = 'Password (min 6 chars)'
            self.fields['locality'].widget.attrs['placeholder'] = 'Colony / Sector / Area'
            self.fields['wage_type'].choices = [
                ('daily', 'Per Day'),
                ('monthly', 'Per Month'),
                ('per_job', 'Per Task')
            ]
            self.fields['trades'].choices = [
                ('Electrician', 'Electrician'),
                ('Plumber', 'Plumber'),
                ('House Maid', 'House Maid'),
                ('Cook', 'Cook / Chef'),
                ('Carpenter', 'Carpenter'),
                ('Painter', 'Painter'),
                ('Gardener', 'Gardener'),
                ('Driver', 'Personal Driver'),
                ('Mechanic', 'Mechanic'),
                ('Construction Worker', 'Construction Worker'),
            ]

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip().replace(' ', '').replace('-', '')
        if not re.search(r'^[6-9]\d{9}$', phone):
            raise forms.ValidationError('Please enter a valid 10-digit Indian mobile number.')
        if UserAccount.objects.filter(phone=phone).exists():
            raise forms.ValidationError('This phone number is already registered. Please log in.')
        return phone

    def clean_trades(self):
        trades = self.cleaned_data.get('trades', [])
        if len(trades) < 1 or len(trades) > 4:
            raise forms.ValidationError('Please select between 1 and 4 trades.')
        return trades


class EmployerRegisterForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full Name'})
    )
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '10-digit Mobile Number'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email Address'})
    )
    password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Password (min 6 chars)'})
    )
    city = forms.CharField(max_length=80, initial='Noida', required=False, widget=forms.HiddenInput())
    locality = forms.CharField(max_length=120, initial='Sector 62', required=False, widget=forms.HiddenInput())
    latitude = forms.FloatField(required=False, widget=forms.HiddenInput())
    longitude = forms.FloatField(required=False, widget=forms.HiddenInput())
    profile_picture_data = forms.CharField(required=False, widget=forms.HiddenInput())
    digilocker_verified = forms.BooleanField(required=False, widget=forms.HiddenInput())

    # DigiLocker Aadhaar Trust Verification Checkbox / Consent
    digilocker_consent = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-emerald-600 rounded'}),
        label='I consent to verify my identity via DigiLocker Sandbox Aadhaar rails.'
    )

    def __init__(self, *args, lang='hi', **kwargs):
        super().__init__(*args, **kwargs)
        if lang == 'hi':
            self.fields['name'].widget.attrs['placeholder'] = 'पूरा नाम'
            self.fields['phone'].widget.attrs['placeholder'] = '10-अंकों का मोबाइल नंबर'
            self.fields['email'].widget.attrs['placeholder'] = 'ईमेल पता (वैकल्पिक)'
            self.fields['password'].widget.attrs['placeholder'] = 'पासवर्ड (कम से कम 6 अक्षर)'
        else:
            self.fields['name'].widget.attrs['placeholder'] = 'Full Name'
            self.fields['phone'].widget.attrs['placeholder'] = '10-digit Mobile Number'
            self.fields['email'].widget.attrs['placeholder'] = 'Email Address (Optional)'
            self.fields['password'].widget.attrs['placeholder'] = 'Password (min 6 chars)'

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip().replace(' ', '').replace('-', '')
        if not re.search(r'^[6-9]\d{9}$', phone):
            raise forms.ValidationError('Please enter a valid 10-digit Indian mobile number.')
        if UserAccount.objects.filter(phone=phone).exists():
            raise forms.ValidationError('This mobile number is already registered. Please log in.')
        return phone


class LoginForm(forms.Form):
    phone = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Mobile Number or Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Password'})
    )

    def __init__(self, *args, lang='hi', **kwargs):
        super().__init__(*args, **kwargs)
        if lang == 'hi':
            self.fields['phone'].widget.attrs['placeholder'] = 'मोबाइल नंबर या ईमेल'
            self.fields['password'].widget.attrs['placeholder'] = 'पासवर्ड'
        else:
            self.fields['phone'].widget.attrs['placeholder'] = 'Mobile Number or Email'
            self.fields['password'].widget.attrs['placeholder'] = 'Password'


class JobCreateForm(forms.Form):
    CATEGORY_CHOICES_EN = [
        ('Electrician', 'Electrician'),
        ('Plumber', 'Plumber'),
        ('House Maid', 'House Maid'),
        ('Cook', 'Cook / Chef'),
        ('Carpenter', 'Carpenter'),
        ('Painter', 'Painter'),
        ('Gardener', 'Gardener'),
        ('Driver', 'Driver'),
        ('Mechanic', 'Mechanic'),
        ('Construction Worker', 'Construction Worker'),
    ]

    CATEGORY_CHOICES_HI = [
        ('Electrician', 'इलेक्ट्रीशियन'),
        ('Plumber', 'प्लंबर'),
        ('House Maid', 'घरेलू सहायिका'),
        ('Cook', 'रसोइया'),
        ('Carpenter', 'बढ़ई'),
        ('Painter', 'पेंटर'),
        ('Gardener', 'माली'),
        ('Driver', 'चालक'),
        ('Mechanic', 'मैकेनिक'),
        ('Construction Worker', 'निर्माण श्रमिक'),
    ]

    WAGE_PERIOD_CHOICES_EN = [
        ('per_job', 'Total for Task'),
        ('daily', 'Per Day'),
        ('monthly', 'Per Month'),
    ]

    WAGE_PERIOD_CHOICES_HI = [
        ('per_job', 'प्रति कार्य (कुल)'),
        ('daily', 'दैनिक (प्रति दिन)'),
        ('monthly', 'मासिक (प्रति माह)'),
    ]

    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-input', 'id': 'job-title-input'})
    )
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES_EN,
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'job-category-select'})
    )
    responsibilities = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input h-20 text-xs', 'id': 'job-tasks-input'})
    )
    duration_number = forms.IntegerField(
        min_value=1, max_value=365, initial=2, required=False,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'id': 'job-duration-number', 'placeholder': '2', 'min': '1'})
    )
    duration_unit = forms.ChoiceField(
        choices=[('hours', 'Hours'), ('days', 'Days'), ('months', 'Months')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'job-duration-unit-select'})
    )
    duration_text = forms.CharField(
        max_length=100, initial='2 Hours', required=False,
        widget=forms.HiddenInput(attrs={'id': 'job-duration-input'})
    )
    offered_price = forms.DecimalField(
        min_value=100, initial=500,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'id': 'job-price-input'})
    )
    wage_period = forms.ChoiceField(
        choices=WAGE_PERIOD_CHOICES_EN,
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'job-wage-period-select'})
    )
    locality = forms.CharField(
        max_length=120, initial='Sector 62, Noida',
        widget=forms.TextInput(attrs={'class': 'form-input', 'id': 'job-locality-input'})
    )
    city = forms.CharField(
        max_length=80, initial='Noida',
        widget=forms.TextInput(attrs={'class': 'form-input', 'id': 'job-city-input'})
    )
    latitude = forms.FloatField(required=False, widget=forms.HiddenInput())
    longitude = forms.FloatField(required=False, widget=forms.HiddenInput())

    # Pre-Signed Contract Terms (Generated dynamically or compiled via Agreement Engine)
    contract_terms = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'w-full bg-white rounded-xl border border-neutral-200 p-4 font-mono text-xs text-neutral-800 leading-relaxed shadow-2xs resize-none focus:outline-none focus:border-neutral-950 transition', 'id': 'contract-terms-area', 'rows': '8', 'readonly': 'readonly'})
    )
    
    # 1st-Party Digital Signature Confirmation (Now captured via dedicated agreement viewer)
    digital_signature_consent = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-neutral-950 rounded focus:ring-neutral-950 cursor-pointer accent-neutral-950'}),
        label='I hereby apply my 1st-Party Digital Consent Signature to this pre-signed contract.'
    )

    def __init__(self, *args, lang='hi', **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        if lang == 'hi':
            self.fields['category'].choices = self.CATEGORY_CHOICES_HI
            self.fields['wage_period'].choices = self.WAGE_PERIOD_CHOICES_HI
            self.fields['duration_unit'].choices = [
                ('hours', 'घंटे'),
                ('days', 'दिन'),
                ('months', 'महीने'),
            ]
            self.fields['title'].widget.attrs['placeholder'] = 'जैसे: किचन पाइपलाइन मरम्मत के लिए प्लंबर की आवश्यकता'
            self.fields['responsibilities'].widget.attrs['placeholder'] = 'वैकल्पिक: कोई विशेष निर्देश (जैसे तीसरी मंजिल, लिफ्ट नहीं है)...'
            self.fields['duration_text'].widget.attrs['placeholder'] = 'जैसे: 2 घंटे, 1 दिन, मासिक'
            self.fields['offered_price'].widget.attrs['placeholder'] = 'जैसे: 600'
            self.fields['locality'].widget.attrs['placeholder'] = 'पता / कॉलोनी / लैंडमार्क'
            self.fields['city'].widget.attrs['placeholder'] = 'शहर'
            self.fields['duration_text'].initial = '2 घंटे'
        else:
            self.fields['category'].choices = self.CATEGORY_CHOICES_EN
            self.fields['wage_period'].choices = self.WAGE_PERIOD_CHOICES_EN
            self.fields['duration_unit'].choices = [
                ('hours', 'Hours'),
                ('days', 'Days'),
                ('months', 'Months'),
            ]
            self.fields['title'].widget.attrs['placeholder'] = 'e.g. Urgent Plumber needed for Kitchen Pipeline Repair'
            self.fields['responsibilities'].widget.attrs['placeholder'] = 'Optional: Any specific note (e.g. 3rd floor, no lift, bring tall ladder)...'
            self.fields['duration_text'].widget.attrs['placeholder'] = 'e.g. 2 Hours, 1 Day, Monthly'
            self.fields['offered_price'].widget.attrs['placeholder'] = 'e.g. 600'
            self.fields['locality'].widget.attrs['placeholder'] = 'Address / Sector / Landmark'
            self.fields['city'].widget.attrs['placeholder'] = 'City'
            self.fields['duration_text'].initial = '2 Hours'

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title', '').strip()
        resp = cleaned_data.get('responsibilities', '').strip()
        if not resp and title:
            cleaned_data['responsibilities'] = title

        num = cleaned_data.get('duration_number')
        unit = cleaned_data.get('duration_unit') or 'hours'
        text = cleaned_data.get('duration_text')

        if num:
            if self.lang == 'hi':
                unit_map = {'hours': 'घंटे', 'days': 'दिन', 'months': 'महीने'}
                u_str = unit_map.get(unit, 'घंटे')
                cleaned_data['duration_text'] = f"{num} {u_str}"
            else:
                unit_map = {
                    'hours': 'Hour' if num == 1 else 'Hours',
                    'days': 'Day' if num == 1 else 'Days',
                    'months': 'Month' if num == 1 else 'Months'
                }
                u_str = unit_map.get(unit, 'Hours')
                cleaned_data['duration_text'] = f"{num} {u_str}"
        elif not text:
            cleaned_data['duration_text'] = '2 घंटे' if self.lang == 'hi' else '2 Hours'

        return cleaned_data
