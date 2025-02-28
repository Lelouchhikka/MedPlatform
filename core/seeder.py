import os
import django
import random
from faker import Faker
from datetime import datetime, timedelta

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_platform.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Doctor, Specialty, Clinic, DoctorSchedule

fake = Faker("ru_RU")
User = get_user_model()

def seed_specialties():
    """Создаёт специальности, если их нет"""
    specialties = ["Кардиолог", "Невролог", "Терапевт", "Дерматолог", "Офтальмолог"]
    specialty_objs = [Specialty.objects.get_or_create(name=name)[0] for name in specialties]
    print(f"✅ Добавлено {len(specialty_objs)} специальностей")
    return specialty_objs

def generate_unique_email():
    """Генерирует уникальный email, избегая повторений"""
    while True:
        email = fake.unique.email()
        if not User.objects.filter(email=email).exists():
            return email

def generate_unique_clinic_name():
    """Генерирует уникальное название клиники"""
    while True:
        name = fake.company()
        if not Clinic.objects.filter(name=name).exists():
            return name
def generate_unique_license():
    """Генерирует уникальный номер лицензии"""
    while True:
        license_number = str(fake.random_int(min=100000, max=999999))  # Генерируем 6-значный номер
        if not Doctor.objects.filter(license_number=license_number).exists():
            return license_number

def seed_clinics(count=5):
    """Создает тестовые клиники"""
    clinics = []
    for _ in range(count):
        email = generate_unique_email()
        username = f"{email.split('@')[0]}_{random.randint(1000, 9999)}"

        user = User.objects.create_user(
            username=username,
            email=email,
            password="password123",
            role="clinic",
        )
        clinic = Clinic.objects.create(
            user=user,
            name=fake.company(),
            address=fake.address(),
            phone=fake.phone_number(),
            email=fake.email(),
            description=fake.text(max_nb_chars=200)
        )
        clinics.append(clinic)

    print(f"✅ Создано {count} клиник")
    return clinics



def seed_doctors(n=10):
    specialties = list(Specialty.objects.all())  # Получаем все специальности
    clinics = list(Clinic.objects.all())  # Получаем все клиники
    doctors = []

    for _ in range(n):
        user = User.objects.create_user(
            username=fake.user_name(),
            email=fake.email(),
            password="password123",
            role="doctor"
        )

        doctor = Doctor.objects.create(
            user=user,
            license_number=generate_unique_license(),
            clinic=random.choice(clinics),
            phone=fake.phone_number(),
            rating=round(random.uniform(3.0, 5.0), 1),
        )

        # ✅ Добавляем несколько случайных специальностей
        num_specialties = random.randint(1, min(3, len(specialties)))  # От 1 до 3 специальностей
        doctor.specialties.set(random.sample(specialties, num_specialties))

        doctors.append(doctor)

    print(f"✅ {n} врачей успешно созданы!")
def seed_schedule():
    print("📅 Генерация расписания для докторов...")
    doctors = Doctor.objects.all()

    start_date = datetime.today().date()
    end_date = start_date + timedelta(days=30)  # Расписание на месяц
    start_time = datetime.strptime("09:00", "%H:%M").time()
    end_time = datetime.strptime("18:00", "%H:%M").time()
    duration = 60  # 1 час на консультацию

    for doctor in doctors:
        DoctorSchedule.generate_schedule(
            doctor=doctor,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            duration=duration,  # Убрали is_recurring
        )

    print("✅ Расписание успешно сгенерировано!")


if __name__ == "__main__":
    seed_specialties()
    seed_clinics(5)
    seed_doctors(10)
    seed_schedule()
