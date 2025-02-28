
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Patient, Doctor, Clinic, TrainingSession, PatientDocument, Consultation, ConsultationDocument, \
    Specialty


class PatientRegisterForm(forms.ModelForm):
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Подтвердите пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        labels = {
            "username": "Пайдаланушы аты",
            "password1": "Құпия сөз",
            "password2": "Құпия сөзді растаңыз",
        }
        help_texts = {
            "username": "Міндетті. 150 таңбадан аспауы керек. Тек әріптер, сандар және @/./+/-/_ рұқсат етіледі.",
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают!")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            Patient.objects.create(user=user)  # Создаем профиль пациента
        return user

class LoginForm(forms.Form):
    username = forms.CharField(label="Имя пользователя")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

class DoctorForm(forms.ModelForm):
    specialties = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Мамандығы"
    )
    is_duty = forms.BooleanField(required=False, label="Дежурный врач")  # ✅ Флаг для дежурного врача
    class Meta:
        model = Doctor
        fields = ["user", "specialties", "clinic", "license_number", "phone", "education", "photo", "experience_years","is_duty"]
        widgets = {
            "user": forms.Select(attrs={"class": "form-control"}),
            "clinic": forms.Select(attrs={"class": "form-control"}),
            "license_number": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "education": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "photo": forms.FileInput(attrs={"class": "form-control"}),
            "experience_years": forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 50}),
        }


class DoctorUpdateForm(forms.ModelForm):
    specialties = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.exclude(name="ВОБ - врач общей практики"),  # Убираем "ВОБ"
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Мамандығы"
    )
    is_duty = forms.BooleanField(required=False, label="Дежурный врач")

    class Meta:
        model = Doctor
        fields = ["specialties", "license_number", "phone", "education", "photo", "experience_years", "is_duty"]

class DoctorCreationForm(forms.ModelForm):
    username = forms.CharField(label="Пайдаланушы аты", max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="Құпия сөз", widget=forms.PasswordInput(attrs={"class": "form-control"}))
    specialties = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Мамандығы"
    )
    is_duty = forms.BooleanField(required=False, label="Дежурный врач")  # ✅ Флаг для дежурного врача
    class Meta:
        model = Doctor
        fields = ["username", "email", "password", "specialties", "license_number", "phone", "education", "photo", "experience_years","is_duty"]
        widgets = {
            "license_number": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "education": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "photo": forms.FileInput(attrs={"class": "form-control"}),
            "experience_years": forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 50}),
        }



class ClinicRegisterForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Clinic
        fields = ["name", "address", "phone", "email", "description"]

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
            role="clinic"
        )
        clinic = super().save(commit=False)
        clinic.user = user
        if commit:
            clinic.save()
        return clinic
class ScheduleForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
    duration = forms.ChoiceField(choices=[(30, "30"), (60, "60")])

class ClinicProfileForm(forms.ModelForm):
    class Meta:
        model = Clinic
        fields = ["name", "address", "city", "phone", "email", "description", "photo"]

class PatientDocumentForm(forms.ModelForm):
    class Meta:
        model = PatientDocument
        fields = ["file"]

class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ["photo", "iin", "phone", "weight", "height", "allergies", "chronic_diseases"]
        widgets = {
            "allergies": forms.Textarea(attrs={"rows": 3}),
            "chronic_diseases": forms.Textarea(attrs={"rows": 3}),
        }

class TrainingSessionForm(forms.ModelForm):
    class Meta:
        model = TrainingSession
        fields = ["date", "start_time", "end_time", "video_link", "description"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "video_link": forms.URLInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ["photo", "phone", "education"]
        widgets = {
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "education": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

class ConsultationSummaryForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['summary']

class ConsultationDocumentForm(forms.ModelForm):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

    class Meta:
        model = ConsultationDocument
        fields = ['file']