from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re
from .models import Profile
from .models import CardType


class ShopOwnerRegistrationForm(UserCreationForm):
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Shop Owner Username'}))
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Shop Owner First Name'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Shop Owner Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class':'form-control','placeholder':'Email Address'}))
    contact_no = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Contact Number'}))
    shop_license_number = forms.CharField(max_length=32, required=True, widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Starts with RSL (Eg: RSL96)'}))
    shop_address = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Address'}))
    place = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Place'}))
    image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class':'form-control-file','accept':'image/*'})
    )
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Password'}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Confirm Password'}))

    class Meta:
        model = User
        fields = ('username','first_name','last_name','email','password1','password2')

    def clean_shop_license_number(self):
        val = self.cleaned_data.get('shop_license_number')
        if not val:
            raise forms.ValidationError('Shop license is required')
        # simple format check: starts with RSL
        if not val.upper().startswith('RSL'):
            raise forms.ValidationError('Shop license must start with RSL')
        if Profile.objects.filter(shop_license_number__iexact=val).exists():
            raise forms.ValidationError('This shop license is already registered')
        return val

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        if commit:
            user.save()
            Profile.objects.update_or_create(user=user, defaults={
                'contact_no': re.sub(r'[^0-9]', '', self.cleaned_data.get('contact_no') or ''),
                'shop_license_number': self.cleaned_data.get('shop_license_number'),
                'shop_address': self.cleaned_data.get('shop_address'),
                'image': self.cleaned_data.get('image'),
                'place': self.cleaned_data.get('place'),
            })
        return user

    def _post_clean(self):
        """Skip Django's global password validators for shop owner signup.

        This keeps the form simple for shop owners; we still ensure model cleaning
        happens but don't run the project-wide password validators.
        """
        from django.forms.models import ModelForm
        ModelForm._post_clean(self)

    def clean_password2(self):
        """Minimal password validation: ensure both passwords match and have at least 3 chars."""
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if not p1 or not p2:
            raise forms.ValidationError('Please enter the password in both fields.')
        if p1 != p2:
            raise forms.ValidationError('The two password fields didn\'t match.')
        if len(p1) < 3:
            raise forms.ValidationError('Password must be at least 3 characters long.')
        return p2


class RegistrationForm(UserCreationForm):
    username = forms.CharField(
        max_length=150, 
        required=True, 
        min_length=3,
        widget=forms.TextInput(attrs={
            'placeholder': 'Username (3-150 characters, letters only)',
            'class': 'form-control',
            'pattern': '^[a-zA-Z]+$',
            'title': 'Username must contain only letters (no numbers or special characters)'
        })
    )
    first_name = forms.CharField(
        max_length=30, 
        required=False, 
        widget=forms.TextInput(attrs={
            'placeholder': 'First name',
            'class': 'form-control'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=False, 
        widget=forms.TextInput(attrs={
            'placeholder': 'Last name',
            'class': 'form-control'
        })
    )
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={
            'placeholder': 'Email address',
            'class': 'form-control',
            'type': 'email'
        })
    )
    password1 = forms.CharField(
        label='Password', 
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password (3-6 digits only)',
            'class': 'form-control'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password', 
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm Password',
            'class': 'form-control'
        })
    )
    address = forms.CharField(
        max_length=255, 
        required=False, 
        widget=forms.TextInput(attrs={
            'placeholder': 'Address',
            'class': 'form-control'
        })
    )
    ration_card_number = forms.CharField(
        max_length=32,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '11 digit Ration Card Number',
            'class': 'form-control'
        })
    )
    family_members = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Total family members (adults + children)'
        })
    )
    ration_card_front = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class':'form-control-file','accept':'image/*'})
    )
    ration_card_back = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class':'form-control-file','accept':'image/*'})
    )
    place = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Place',
            'class': 'form-control'
        })
    )
    contact_no = forms.CharField(
        max_length=15, 
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Contact Number (10-15 digits)',
            'class': 'form-control',
            'pattern': '^[0-9]{10,15}$',
            'title': 'Contact number must be 10-15 digits'
        })
    )
    image = forms.ImageField(
        required=False, 
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control-file',
            'accept': 'image/*'
        })
    )
    card_type = forms.ModelChoiceField(
        queryset=CardType.objects.all(),
        required=False,
        empty_label='Select card type',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email', 'password1', 'password2',
        )

    def save(self, commit=True):
        user = super().save(commit=commit)
        # Create or update profile
        Profile.objects.update_or_create(
            user=user,
            defaults={
                'address': self.cleaned_data.get('address'),
                'contact_no': re.sub(r'[^0-9]', '', (self.cleaned_data.get('contact_no') or '')),
                'image': self.cleaned_data.get('image'),
                'ration_card_number': self.cleaned_data.get('ration_card_number'),
                'family_members': self.cleaned_data.get('family_members'),
                'ration_card_front': self.cleaned_data.get('ration_card_front'),
                'ration_card_back': self.cleaned_data.get('ration_card_back'),
                'place': self.cleaned_data.get('place'),
                'card_type': self.cleaned_data.get('card_type'),
            }
        )
        return user

    def _post_clean(self):
        """
        Override to avoid Django's built-in password validators so we can
        enforce a custom numeric-only 3-6 length password policy instead.
        """
        # Call ModelForm._post_clean directly to skip UserCreationForm's
        # password validation which enforces global validators.
        from django.forms.models import ModelForm
        ModelForm._post_clean(self)

    def clean_username(self):
        """Validate username for uniqueness and format."""
        username = self.cleaned_data.get('username')
        if not username:
            raise forms.ValidationError('Username is required.')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('A user with this username already exists.')
        
        # Validate username format (letters only)
        if not re.match(r'^[a-zA-Z]+$', username):
            raise forms.ValidationError('Username must contain only letters (no numbers or special characters).')
        
        # Check minimum length
        if len(username) < 3:
            raise forms.ValidationError('Username must be at least 3 characters long.')
        
        return username

    def clean_email(self):
        """Validate email for format and uniqueness."""
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('Email is required.')
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        
        # Basic email format validation (Django's EmailField already does this, but let's be explicit)
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise forms.ValidationError('Please enter a valid email address.')
        
        return email

    def clean_contact_no(self):
        """Validate contact number for format and uniqueness."""
        contact_no = self.cleaned_data.get('contact_no')
        if not contact_no:
            raise forms.ValidationError('Contact number is required.')
        
        # Remove any non-digit characters
        contact_no = re.sub(r'[^\d]', '', contact_no)
        
        # Check if contact number already exists in Profile
        if Profile.objects.filter(contact_no=contact_no).exists():
            raise forms.ValidationError('A user with this contact number already exists.')
        
        # Validate length (10-15 digits)
        if not (10 <= len(contact_no) <= 15):
            raise forms.ValidationError('Contact number must be between 10 and 15 digits.')
        
        # Check if it contains only digits
        if not contact_no.isdigit():
            raise forms.ValidationError('Contact number must contain only digits.')
        
        return contact_no

    def clean_ration_card_number(self):
        """Validate ration card number format and uniqueness."""
        rc = self.cleaned_data.get('ration_card_number')
        if not rc:
            return rc
        # Normalize: remove spaces
        rc_norm = rc.replace(' ', '')
        # Basic format: alphanumeric, at least 8-32 chars, prefer 11
        if not re.match(r'^[A-Za-z0-9]+$', rc_norm):
            raise forms.ValidationError('Ration card number must be alphanumeric.')
        if len(rc_norm) < 8:
            raise forms.ValidationError('Ration card number looks too short.')
        # Check uniqueness on Profile
        if Profile.objects.filter(ration_card_number__iexact=rc_norm).exists():
            raise forms.ValidationError('This ration card number is already registered.')
        return rc_norm

    def clean_password2(self):
        """Validate that the two password entries match and satisfy the
        numeric-only 3-6 characters rule.
        """
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if not p1 or not p2:
            raise forms.ValidationError('Please enter the password in both fields.')
        if p1 != p2:
            raise forms.ValidationError('The two password fields didn\'t match.')
        # Enforce numeric-only
        if not p1.isdigit():
            raise forms.ValidationError('Password must contain only digits.')
        # Enforce length 3-6
        if not (3 <= len(p1) <= 6):
            raise forms.ValidationError('Password must be between 3 and 6 digits long.')
        return p2
