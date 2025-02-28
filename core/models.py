from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from datetime import datetime, timedelta

from django.utils.timezone import now


class UserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username field must be set")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('clinic', 'Clinic'),  # 🔹 Добавили роль для клиники
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)
    objects = UserManager()

    def __str__(self):
        return self.username

class Specialty(models.Model):
    """ Таблица специальностей врачей """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to="patient_photos/", blank=True, null=True,verbose_name="Фото")  # ✅ Поле для фото
    iin = models.CharField(default="Не указано",blank=True,max_length=12, verbose_name="ЖСН")
    phone = models.CharField(default="Не указано",blank=True,max_length=15, verbose_name="Телефон")
    weight = models.FloatField(default=0,blank=True,verbose_name="Салмақ")
    height = models.FloatField(default=0,blank=True,verbose_name="Бойы")
    allergies = models.TextField(default="Не указано",blank=True, verbose_name="Аллергиялар")  # ✅ Добавили значение по умолчанию
    chronic_diseases = models.TextField(default="Не указано",blank=True, verbose_name="Созылмалы аурулар")

    def __str__(self):
        return self.user.username


class PatientDocument(models.Model):
    """ Документы пациентов """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to="patient_documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Документ {self.patient.user.username}"


class Clinic(models.Model):
    """ Таблица клиник """
    name = models.CharField(max_length=255)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="clinic_account", null=True, blank=True)  # временно nullable
    city = models.CharField(max_length=255)
    email=models.TextField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255)
    description = models.TextField()
    rating = models.FloatField(default=0.0)
    photo = models.ImageField(upload_to='clinics/', blank=True, null=True)
    phone = models.CharField(max_length=20,null=True)
    def __str__(self):
        return self.name

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor")
    specialties = models.ManyToManyField(Specialty, related_name="doctors", verbose_name="Мамандығы") # 🔹 Проверьте это
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="doctors", default=1)
    license_number = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20)
    education = models.TextField()
    rating = models.FloatField(default=0.0)
    photo = models.ImageField(upload_to="doctors/", null=True, blank=True)
    experience_years = models.PositiveIntegerField(default=0, verbose_name="Стаж работы (лет)")  # Новое поле
    is_duty = models.BooleanField(default=False, verbose_name="Дежурный врач")  # ✅ Флаг для дежурного врача

    def save(self, *args, **kwargs):
        """ Автоматически добавляем или удаляем специальность 'ВОБ - врач общей практики' """
        super().save(*args, **kwargs)
        wob_specialty, created = Specialty.objects.get_or_create(name="ВОБ - врач общей практики")

        if self.is_duty:
            self.specialties.add(wob_specialty)
        else:
            self.specialties.remove(wob_specialty)
    def get_experience_years(self):
        return now().year - self.experience_start_year
    def get_specialties(self):
        specialties = self.specialties.all().values_list('name', flat=True)


        return ", ".join(specialties)
    def __str__(self):
        return f"{self.user.get_full_name()} "

from datetime import datetime, timedelta

class DoctorSchedule(models.Model):
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE, related_name="schedule")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    @classmethod
    def generate_duty_schedule(cls, doctor, start_date, end_date):
        """ Генерация расписания 24/7 для дежурных врачей """
        slots = []
        current_date = start_date

        # Временные интервалы для перерывов
        breaks = [
            ("08:00", "09:00"),  # Завтрак
            ("13:00", "14:00"),  # Обед
            ("19:00", "20:00")  # Ужин
        ]

        while current_date <= end_date:
            for hour in range(24):
                start_time = datetime.strptime(f"{hour:02d}:00", "%H:%M").time()
                end_time = (datetime.combine(datetime.today(), start_time) + timedelta(hours=1)).time()

                # Проверяем на дублирование
                if cls.objects.filter(doctor=doctor, date=current_date, start_time=start_time).exists():
                    continue

                # Проверяем, попадает ли на перерыв
                is_break = any(
                    start_time >= datetime.strptime(b[0], "%H:%M").time() and
                    start_time < datetime.strptime(b[1], "%H:%M").time()
                    for b in breaks
                )

                if not is_break:
                    slots.append(cls(
                        doctor=doctor,
                        date=current_date,
                        start_time=start_time,
                        end_time=end_time
                    ))

            current_date += timedelta(days=1)

        cls.objects.bulk_create(slots)
    @classmethod
    def generate_schedule(cls, doctor, start_date, end_date, start_time, end_time, duration):
        slots = []
        current_date = start_date

        # 🔥 УБЕДИМСЯ, ЧТО duration — ЭТО INT
        duration = int(duration)

        while current_date <= end_date:
            current_time = start_time

            while current_time < end_time:
                start_slot_datetime = datetime.combine(current_date, current_time)
                end_slot_datetime = start_slot_datetime + timedelta(minutes=duration)

                slots.append(cls(
                    doctor=doctor,
                    date=current_date,
                    start_time=start_slot_datetime.time(),
                    end_time=end_slot_datetime.time()
                ))

                current_time = end_slot_datetime.time()

            current_date += timedelta(days=1)

        cls.objects.bulk_create(slots)


class Consultation(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)  # ❗ Было User, теперь Patient
    schedule = models.ForeignKey(DoctorSchedule, on_delete=models.CASCADE)
    video_link = models.URLField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)


    def __str__(self):
        return f"Консультация {self.doctor.user.username} с {self.patient.user.username} ({self.schedule.date} {self.schedule.start_time})"


class ConsultationDocument(models.Model):
    """ Документы пациентов """
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to="consultation_documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Документ {self.consultation.doctor.user.username}"


class DoctorReview(models.Model):
    doctor = models.ForeignKey("Doctor", on_delete=models.CASCADE)
    patient = models.ForeignKey("Patient", on_delete=models.CASCADE)
    consultation = models.OneToOneField("Consultation", on_delete=models.CASCADE, null=True, blank=True)  # ✅ Добавлено null=True, blank=True
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('patient', 'consultation')  # Чтобы пациент мог оставить только один отзыв


class TrainingSession(models.Model):
    organizer = models.ForeignKey('Doctor', on_delete=models.CASCADE, related_name="organized_trainings")
    specialty = models.ForeignKey('Specialty', on_delete=models.CASCADE, related_name="trainings")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    video_link = models.URLField()
    description = models.TextField()
    participants = models.ManyToManyField('Doctor', related_name="trainings_attended", blank=True)

    def __str__(self):
        return f"Тренинг {self.specialty.name} от {self.organizer.user.username} ({self.date})"