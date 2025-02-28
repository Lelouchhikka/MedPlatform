import logging

from django.db.models import Avg
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import datetime
from datetime import timedelta, date

from django.views.decorators.csrf import csrf_exempt

from .models import User, Doctor, Clinic, Specialty, DoctorSchedule, Consultation, Patient, TrainingSession, \
    ConsultationDocument, DoctorReview
from .forms import ScheduleForm, DoctorForm, ClinicRegisterForm, TrainingSessionForm, DoctorProfileForm, \
    PatientProfileForm, PatientDocumentForm, ClinicProfileForm, ConsultationSummaryForm, ConsultationDocumentForm, \
    PatientRegisterForm, DoctorCreationForm, DoctorUpdateForm
import locale
from django.utils.timezone import now
from babel.dates import format_date

locale.setlocale(locale.LC_TIME, 'kk_KZ.utf8')
MONTHS_KZ = {
    "January": "Қаңтар",
    "February": "Ақпан",
    "March": "Наурыз",
    "April": "Сәуір",
    "May": "Мамыр",
    "June": "Маусым",
    "July": "Шілде",
    "August": "Тамыз",
    "September": "Қыркүйек",
    "October": "Қазан",
    "November": "Қараша",
    "December": "Желтоқсан",
}

def localize_date(date):
    return format_date(date, format='d MMMM yyyy', locale='ru')
def home(request):
    return render(request, "core/home.html")

# 🏥 Регистрация пациента
def register(request):
    if request.method == "POST":
        form = PatientRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматически авторизуем
            messages.success(request, "Регистрация успешна! Теперь заполните профиль.")
            return redirect("patient_profile")  # Редирект в профиль
    else:
        form = PatientRegisterForm()

    return render(request, "core/auth/register.html", {"form": form})

# 🔑 Авторизация
def user_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Неверный логин или пароль")
    return render(request, "core/auth/login.html")








@login_required
def delete_schedule_day(request, date):
    """
    Удаление всех слотов за выбранный день.
    """
    doctor = request.user.doctor  # Получаем врача
    slots = DoctorSchedule.objects.filter(doctor=doctor, date=date, is_booked=False)

    if not slots.exists():
        messages.error(request, "Невозможно удалить — либо нет слотов, либо они уже забронированы.")
    else:
        slots.delete()
        messages.success(request, f"Все слоты на {date} удалены.")

    return redirect("view_schedule")

logger = logging.getLogger(__name__)  # Логгер

@login_required
def clinic_profile(request):
    clinic = get_object_or_404(Clinic, user=request.user)

    if request.method == "POST":
        form = ClinicProfileForm(request.POST, request.FILES, instance=clinic)
        if form.is_valid():
            form.save()
            return redirect("clinic_profile")
    else:
        form = ClinicProfileForm(instance=clinic)

    doctors = Doctor.objects.filter(clinic=clinic)

    return render(request, "core/clinics/clinic_profile.html", {
        "form": form,
        "clinic": clinic,
        "doctors": doctors
    })

from datetime import date, timedelta, datetime, time
from django.http import JsonResponse
from core.models import DoctorSchedule

def create_next_month_schedule(request):
    doctor = request.user.doctor  # Получаем текущего врача

    # Определяем первый день следующего месяца
    today = date.today()
    first_day_next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)

    # Проверяем, есть ли уже слоты на этот месяц
    existing_slots = DoctorSchedule.objects.filter(
        doctor=doctor,
        date__year=first_day_next_month.year,
        date__month=first_day_next_month.month
    )

    print(f"Найдено слотов на {first_day_next_month.strftime('%B %Y')}: {existing_slots.count()}")

    if existing_slots.exists():
        print("⚠ Удаление старых слотов...")
        existing_slots.delete()  # Удаляем старые слоты

    # Создаём новое расписание
    new_slots = []
    for day in range(1, 32):  # Добавляем все дни месяца
        try:
            new_date = first_day_next_month.replace(day=day)
        except ValueError:
            break  # Если день выходит за пределы месяца, выходим из цикла

        for hour in range(9, 18):  # Время с 9:00 до 17:00
            start_time = time(hour, 0)  # Начало приёма (например, 09:00)
            end_time = time(hour + 1, 0)  # Конец приёма (на 1 час позже)

            new_slots.append(DoctorSchedule(
                doctor=doctor,
                date=new_date,
                start_time=start_time,
                end_time=end_time,  # ✅ Добавляем обязательное поле
                is_booked=False
            ))

    DoctorSchedule.objects.bulk_create(new_slots)
    print(f"✅ Создано {len(new_slots)} слотов на {first_day_next_month.strftime('%B %Y')}")

    return JsonResponse({"success": f"Создано {len(new_slots)} слотов на {first_day_next_month.strftime('%B %Y')}"})

@login_required
def patient_consultations(request):
    if request.user.role != 'patient':
        return redirect('home')

    consultations = Consultation.objects.filter(patient__user=request.user).order_by("-schedule__date")
    return render(request, "core/client/patient_consultations.html", {"consultations": consultations})

def clinic_detail(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)
    doctors = Doctor.objects.filter(clinic=clinic)

    return render(request, "core/clinics/clinic_detail.html", {"clinic": clinic, "doctors": doctors})
# 🚪 Выход из системы
def user_logout(request):
    logout(request)
    return redirect("home")

# 📋 Список врачей
def doctor_list(request):
    doctors = Doctor.objects.all()
    return render(request, "core/doctor/doctors.html", {"doctors": doctors})

# 🏥 Список клиник
def clinic_list(request):
    clinics = Clinic.objects.all()
    return render(request, "core/clinics/clinics.html", {"clinics": clinics})

# 🩺 Выбор специальности
def specialties_list(request):
    specialties = Specialty.objects.all()
    return render(request, "core/doctor/specialties.html", {"specialties": specialties})

# 🔎 Список врачей по специальности
def doctors_by_specialty(request, specialty_id):
    specialty = get_object_or_404(Specialty, id=specialty_id)
    doctors = Doctor.objects.filter(specialties=specialty)
    return render(request, "core/doctor/doctors_by_specialty.html", {"doctors": doctors, "specialty": specialty})

# 🗓️ Просмотр расписания врача
def doctor_schedule(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    unique_dates = DoctorSchedule.objects.filter(doctor=doctor, is_booked=False) \
        .values_list('date', flat=True).distinct()

    reviews = DoctorReview.objects.filter(doctor=doctor).order_by("-created_at")
    doctor.average_rating = DoctorReview.objects.filter(doctor=doctor).aggregate(Avg('rating'))['rating__avg']

    return render(request, "core/client/doctor_schedule.html", {
        "doctor": doctor,
        "unique_dates": unique_dates,
        "reviews": reviews,
    })

def available_times(request, doctor_id):
    date_str = request.GET.get("date")
    doctor = get_object_or_404(Doctor, id=doctor_id)

    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        slots = DoctorSchedule.objects.filter(doctor=doctor, date=selected_date, is_booked=False)

        times = [{"id": slot.id, "start_time": slot.start_time.strftime("%H:%M")} for slot in slots]
        return JsonResponse({"times": times})

    except ValueError:
        return JsonResponse({"error": "Неверный формат даты"}, status=400)

def get_schedule_by_date(request, doctor_id):
    date_str = request.GET.get("date")  # Получаем дату из GET-запроса

    print(f"📅 Получена дата от фронтенда: {date_str}")  # Логирование

    if not date_str:
        return JsonResponse({"error": "Дата не передана"}, status=400)

    try:
        # Используем `datetime.strptime()` для преобразования строки в объект `date`
        selected_date = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        print(f"✅ Дата успешно преобразована: {selected_date}")  # Логирование

        doctor = get_object_or_404(Doctor, id=doctor_id)
        slots = DoctorSchedule.objects.filter(
            doctor=doctor, date=selected_date, is_booked=False
        ).order_by("start_time")

        times = [{"id": slot.id, "start_time": slot.start_time.strftime("%H:%M")} for slot in slots]
        return JsonResponse({"times": times})

    except ValueError as e:
        print(f"❌ Ошибка преобразования даты: {e}")  # Логирование ошибки
        return JsonResponse({"error": "Неверный формат даты! Ожидается YYYY-MM-DD."}, status=400)

def format_date_kz(date):
    month_en = date.strftime("%B")  # Получаем название месяца на английском
    month_kz = MONTHS_KZ.get(month_en, month_en)  # Заменяем на казахский
    return date.strftime(f"%d {month_kz} %Y")  # Формируем дату
@login_required
def get_doctor_schedule_by_date(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    date_str = request.GET.get("date")

    if not date_str:
        return JsonResponse({"error": "Дата не передана"}, status=400)

    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        slots = DoctorSchedule.objects.filter(doctor=doctor, date=selected_date).order_by("start_time").distinct()

        times = []
        seen_times = set()  # Используем set для предотвращения дубликатов

        for slot in slots:
            if slot.start_time not in seen_times:
                consultation = Consultation.objects.filter(schedule=slot).first()
                times.append({
                    "id": slot.id,
                    "start_time": slot.start_time.strftime("%H:%M"),
                    "is_booked": slot.is_booked,
                    "consultation_id": consultation.id if consultation else None,
                    "video_link": consultation.video_link if consultation else None,
                    "summary": consultation.summary if consultation else None
                })
                seen_times.add(slot.start_time)  # Запоминаем время, чтобы не дублировать

        return JsonResponse({"times": times})

    except ValueError:
        return JsonResponse({"error": "Неверный формат даты. Ожидается YYYY-MM-DD."}, status=400)



@login_required
def add_video_link(request, schedule_id):
    print('qwe')
    print(schedule_id)
    consultation = get_object_or_404(Consultation, schedule_id=schedule_id)

    if request.method == "POST":
        video_link = request.POST.get("video_link")
        consultation.video_link = video_link
        consultation.save()
        return redirect("view_schedule")

    return render(request, "core/doctor/add_video_link.html", {"consultation": consultation})


@login_required
def add_consultation_summary(request, schedule_id):
    consultation = get_object_or_404(Consultation, schedule_id=schedule_id)

    if request.method == "POST":
        summary_form = ConsultationSummaryForm(request.POST, instance=consultation)
        document_form = ConsultationDocumentForm(request.POST, request.FILES)

        if summary_form.is_valid():
            summary_form.save()

        if document_form.is_valid():
            for file in request.FILES.getlist('file'):
                ConsultationDocument.objects.create(consultation=consultation, file=file)

            messages.success(request, "Итоги консультации сохранены, документы загружены!")
            return redirect("view_schedule")

    else:
        summary_form = ConsultationSummaryForm(instance=consultation)
        document_form = ConsultationDocumentForm()

    return render(request, "core/doctor/add_consultation_summary.html", {
        "summary_form": summary_form,
        "document_form": document_form,
        "consultation": consultation
    })

def consent_view(request):
    return render(request, "core/client/consent.html")
@login_required
def delete_schedule_slot(request, schedule_id):
    """
    Удаление слота, если он не забронирован.
    """
    slot = get_object_or_404(DoctorSchedule, id=schedule_id, doctor__user=request.user)

    if slot.is_booked:
        return JsonResponse({"error": "Нельзя удалить забронированный слот!"}, status=400)

    slot.delete()

    # ✅ Всегда возвращаем JSON-ответ
    return JsonResponse({"message": "Слот удален успешно."}, status=200, safe=False)


# 📆 Врач создаёт расписание



@login_required
def create_schedule(request):
    if request.method == "POST":
        print(request.POST)  # Отобразит данные формы в терминале
        form = ScheduleForm(request.POST)
        if form.is_valid():
            doctor = Doctor.objects.get(user=request.user)
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]
            start_time = form.cleaned_data["start_time"]
            end_time = form.cleaned_data["end_time"]
            duration = int(form.cleaned_data["duration"])
            print(f"Создание расписания: {start_date} - {end_date}, {start_time} - {end_time}, шаг {duration} минут")
            if doctor.is_duty:
                start_date = datetime.today().date()
                end_date = start_date + timedelta(days=30)  # На месяц вперед
                DoctorSchedule.generate_duty_schedule(doctor, start_date, end_date)
            else:
            # Генерация расписания
                DoctorSchedule.generate_schedule(
                doctor=doctor,
                start_date=start_date,
                end_date=end_date,
                start_time=start_time,
                end_time=end_time,
                duration=duration
                )
            messages.success(request, "Расписание успешно создано!")
            return redirect("view_schedule")
        else:
            print("Форма не валидна", form.errors)
    else:
        form = ScheduleForm()

    return render(request, "core/doctor/create_schedule_next_month.html", {"form": form})


# 👀 Врач смотрит своё расписание
@login_required
def view_schedule(request):
    doctor = request.user.doctor  # Получаем текущего врача
    schedules = DoctorSchedule.objects.filter(doctor=doctor).order_by("date", "start_time")

    # Извлекаем только уникальные даты (убираем дубликаты)
    unique_dates = sorted(set(schedule.date for schedule in schedules))

    return render(request, "core/doctor/view_schedule.html", {
        "doctor": doctor,
        "schedule_dates": unique_dates
    })

# ✏️ Врач редактирует расписание
@login_required
def edit_schedule(request, schedule_id):
    if request.user.role != 'doctor':
        return redirect('home')

    slot = get_object_or_404(DoctorSchedule, id=schedule_id, doctor__user=request.user)

    if request.method == "POST":
        form = ScheduleForm(request.POST)
        if form.is_valid():
            slot.date = form.cleaned_data["start_date"]
            slot.start_time = form.cleaned_data["start_time"]
            slot.end_time = form.cleaned_data["end_time"]
            slot.duration = form.cleaned_data["duration"]
            slot.save()

            messages.success(request, "Расписание обновлено!")
            return redirect("view_schedule")
    else:
        form = ScheduleForm(initial={
            "start_date": slot.date,
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "duration": slot.duration
        })

    return render(request, "core/doctor/edit_schedule.html", {"form": form, "slot": slot})

# 📌 Пациент записывается к врачу
@login_required
def book_appointment(request, schedule_id):

    slot = get_object_or_404(DoctorSchedule, id=schedule_id, is_booked=False)

    if request.user.role != "patient":
        messages.error(request, "Только пациенты могут записываться на приём.")
        return redirect("home")

    patient = get_object_or_404(Patient, user=request.user)  # Теперь получаем `Patient`

    consultation = Consultation.objects.create(
        doctor=slot.doctor,
        patient=patient,  # ✅ Теперь передаем объект Patient, а не User
        schedule=slot
    )

    slot.is_booked = True
    slot.save()

    messages.success(request, "Вы успешно записаны на приём!")
    return redirect("appointment_success", consultation.id)

@login_required
def delete_schedule(request, schedule_id):
    if request.user.role != 'doctor':
        return redirect('home')

    slot = get_object_or_404(DoctorSchedule, id=schedule_id, doctor__user=request.user)

    if slot.is_booked:
        messages.error(request, "Нельзя удалить забронированное расписание.")
    else:
        slot.delete()
        messages.success(request, "Расписание успешно удалено.")

    return redirect("view_schedule")
# ✅ Подтверждение записи
@login_required
def appointment_success(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id, patient__user=request.user)
    return render(request, "core/client/appointment_success.html", {"consultation": consultation})




# 🏥 Регистрация клиники
def register_clinic(request):
    if request.method == "POST":
        form = ClinicRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Клиника успешно зарегистрирована! Теперь войдите в систему.")
            return redirect("login")
    else:
        form = ClinicRegisterForm()
    return render(request, "core/auth/register_clinic.html", {"form": form})

# 🔑 Авторизация клиники
def clinic_dashboard(request):
    if request.user.is_authenticated and request.user.role == "clinic":
        clinic = get_object_or_404(Clinic, user=request.user)
        doctors = Doctor.objects.filter(clinic=clinic)
        return render(request, "core/clinics/clinic_dashboard.html", {"clinic": clinic, "doctors": doctors})
    return redirect("login")

# 🩺 Добавление врача клиникой
def add_doctor(request):
    if request.method == "POST":
        form = DoctorCreationForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            is_duty = form.cleaned_data["is_duty"]

            # Проверяем уникальность
            if User.objects.filter(username=username).exists():
                messages.error(request, "Бұл пайдаланушы аты қолданыста!")
                return redirect("add_doctor")
            if User.objects.filter(email=email).exists():
                messages.error(request, "Бұл Email қолданыста!")
                return redirect("add_doctor")

            # Создаем пользователя
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role="doctor"  # Назначаем роль "doctor"
            )

            # ✅ Получаем клинику через обратную связь
            try:
                clinic = request.user.clinic_account
            except Clinic.DoesNotExist:
                messages.error(request, "Клиника тіркелмеген. Администраторға хабарласыңыз.")
                return redirect("add_doctor")

            # ✅ Создаем врача и связываем с клиникой
            doctor = form.save(commit=False)
            doctor.user = user
            doctor.clinic = clinic
            doctor.is_duty = is_duty  # Устанавливаем статус дежурного врача
            doctor.save()
            form.save_m2m()  # Сохраняем ManyToMany связи

            # ✅ Добавляем специальность "ВОБ - врач общей практики" для дежурных врачей
            if is_duty:
                wob_specialty, created = Specialty.objects.get_or_create(name="ВОБ - врач общей практики")
                doctor.specialties.add(wob_specialty)

                # ✅ Генерируем расписание 24/7 с перерывами
                start_date = datetime.today().date()
                end_date = start_date + timedelta(days=30)  # Расписание на месяц вперед
                DoctorSchedule.generate_duty_schedule(doctor, start_date, end_date)

            messages.success(request, "Дәрігер сәтті қосылды!")
            return redirect("clinic_dashboard")
        else:
            print(form.errors)

    else:
        form = DoctorCreationForm()

    return render(request, "core/clinics/add_doctor.html", {"form": form})

@login_required
def edit_doctor(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id, clinic=request.user.clinic_account)  # Только врачи этой клиники

    if request.method == "POST":
        form = DoctorUpdateForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            is_duty = form.cleaned_data["is_duty"]

            # ✅ Проверяем статус дежурного врача
            if is_duty != doctor.is_duty:
                doctor.is_duty = is_duty
                # ✅ Удаляем старое расписание
                DoctorSchedule.objects.filter(doctor=doctor).delete()

                if is_duty:
                    # ✅ Добавляем "ВОБ" только если дежурный врач
                    wob_specialty, _ = Specialty.objects.get_or_create(name="ВОБ - врач общей практики")
                    doctor.specialties.add(wob_specialty)
                    # ✅ Генерация 24/7 расписания
                    start_date = datetime.today().date()
                    end_date = start_date + timedelta(days=30)
                    DoctorSchedule.generate_duty_schedule(doctor, start_date, end_date)
                else:
                    # ✅ Убираем "ВОБ" если не дежурный
                    wob_specialty = Specialty.objects.filter(name="ВОБ - врач общей практики").first()
                    if wob_specialty:
                        doctor.specialties.remove(wob_specialty)

            form.save()
            messages.success(request, "Дәрігер сәтті жаңартылды!")
            return redirect("clinic_dashboard")
        else:
            messages.error(request, "Қате! Мәліметтерді сақтауда қате орын алды.")
    else:
        form = DoctorUpdateForm(instance=doctor)

    return render(request, "core/clinics/edit_doctor.html", {"form": form, "doctor": doctor})
# 🗑️ Удаление врача
@login_required
def delete_doctor(request, doctor_id):
    if request.user.role != "clinic":
        return redirect("home")

    clinic = get_object_or_404(Clinic, user=request.user)
    doctor = get_object_or_404(Doctor, id=doctor_id, clinic=clinic)

    if request.method == "POST":
        doctor.delete()
        messages.success(request, "Врач успешно удалён!")
        return redirect("clinic_dashboard")

    return render(request, "core/clinics/delete_doctor.html", {"doctor": doctor})

@login_required
def create_training(request):
    doctor = get_object_or_404(Doctor, user=request.user)

    # Проверяем, есть ли у врача 5+ лет стажа
    experience_years = (datetime.now().year - doctor.experience_years)
    if experience_years < 5:
        messages.error(request, "Вы должны иметь минимум 5 лет стажа, чтобы создавать обучающие созвоны.")
        return redirect("home")

    if request.method == "POST":
        form = TrainingSessionForm(request.POST)
        if form.is_valid():
            training = form.save(commit=False)
            training.organizer = doctor
            training.specialty = doctor.specialty
            training.save()
            messages.success(request, "Обучающий созвон успешно создан!")
            return redirect("trainings_list")
    else:
        form = TrainingSessionForm()

    return render(request, "core/doctor/create_training.html", {"form": form})

# 📌 Список всех обучающих созвонов
@login_required
def trainings_list(request):
    trainings = TrainingSession.objects.all().order_by("-date", "start_time")
    return render(request, "core/doctor/trainings_list.html", {"trainings": trainings})

# 📌 Запись врача на обучающий созвон

def join_training(request, training_id):
    training = get_object_or_404(TrainingSession, id=training_id)
    doctor = get_object_or_404(Doctor, user=request.user)

    # Проверяем, есть ли у доктора забронированные слоты в это же время
    conflicting_schedules = DoctorSchedule.objects.filter(
        doctor=doctor,
        date=training.date,
        start_time__lte=training.end_time,
        end_time__gte=training.start_time,
        is_booked=True
    )

    if conflicting_schedules.exists():
        messages.error(request, "Вы не можете записаться на этот тренинг, так как у вас уже есть консультация в это время.")
        return redirect("trainings_list")

    # Добавляем запись на тренинг
    training.participants.add(doctor)
    messages.success(request, "Вы успешно записались на тренинг!")
    return redirect("trainings_list")

@login_required
def patient_profile(request):
    patient = get_object_or_404(Patient, user=request.user)

    if request.method == "POST":
        form = PatientProfileForm(request.POST, request.FILES, instance=patient)
        doc_form = PatientDocumentForm(request.POST, request.FILES)

        if "save_profile" in request.POST:  # ✅ Если нажали "Сохранить профиль"
            if form.is_valid():
                form.save()
                messages.success(request, "Профиль успешно обновлен!")
                return redirect("patient_profile")

        elif "upload_document" in request.POST:  # ✅ Если загрузили документ
            if doc_form.is_valid():
                document = doc_form.save(commit=False)
                document.patient = patient
                document.save()
                messages.success(request, "Документ успешно загружен!")
                return redirect("patient_profile")

    else:
        form = PatientProfileForm(instance=patient)
        doc_form = PatientDocumentForm()

    documents = patient.documents.all()  # ✅ Получаем все документы пациента

    return render(request, "core/client/patient_profile.html", {
        "form": form,
        "doc_form": doc_form,
        "patient": patient,
        "documents": documents,
    })
@login_required
def doctor_patient_profile(request, patient_id):
    """Доктор просматривает профиль пациента, если у них есть консультация"""
    patient = get_object_or_404(Patient, id=patient_id)

    # Проверяем, есть ли у доктора консультации с этим пациентом
    consultations = Consultation.objects.filter(doctor=request.user.doctor, patient=patient)

    if not consultations.exists():
        return render(request, "core/errors/no_access.html", {"message": "У вас нет доступа к профилю пациента."})

    return render(request, "core/doctor/patient_profile.html", {"patient": patient, "consultations": consultations})
@login_required
def consultation_history(request):
    patient = get_object_or_404(Patient, user=request.user)
    consultations = Consultation.objects.filter(patient=patient).order_by("-schedule__date")
    return render(request, "core/client/consultation_history.html", {"consultations": consultations})

def add_review(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id, patient=request.user.patient)

    if request.method == "POST":
        rating = int(request.POST.get("rating"))
        comment = request.POST.get("comment", "")

        if not (1 <= rating <= 5):
            messages.error(request, "Бағалау 1-ден 5-ке дейін болуы керек")
            return redirect("consultation_history")

        # Проверяем, оставлял ли пациент уже отзыв
        if DoctorReview.objects.filter(consultation=consultation).exists():
            messages.error(request, "Сіз бұл консультацияға пікір қалдырдыңыз!")
            return redirect("consultation_history")

        DoctorReview.objects.create(
            doctor=consultation.doctor,
            patient=request.user.patient,
            consultation=consultation,
            rating=rating,
            comment=comment
        )

        messages.success(request, "Сіздің пікіріңіз сақталды!")
        return redirect("consultation_history")

    return redirect("consultation_history")

@login_required
def doctor_consultation_history(request):
    doctor = get_object_or_404(Doctor, user=request.user)

    consultations = Consultation.objects.filter(doctor=doctor).order_by("-schedule__date")

    return render(request, "core/doctor/consultation_history.html", {
        "consultations": consultations
    })
@login_required
def doctor_profile(request):
    doctor = get_object_or_404(Doctor, user=request.user)

    if request.method == "POST":
        # Обновление фото
        if 'photo' in request.FILES:
            doctor.photo = request.FILES['photo']

        # Обновление данных
        doctor.user.username = request.POST.get('username', doctor.user.username)
        doctor.license_number = request.POST.get('license_number', doctor.license_number)
        doctor.phone = request.POST.get('phone', doctor.phone)
        doctor.education = request.POST.get('education', doctor.education)

        doctor.user.save()
        doctor.save()
        messages.success(request, "Данные успешно обновлены!")

    # Фильтр для показа консультаций без ссылок или итогов
    consultations = Consultation.objects.filter(doctor=doctor)
    filter_no_video = request.GET.get("no_video")
    filter_no_summary = request.GET.get("no_summary")

    if filter_no_video:
        consultations = consultations.filter(video_link__isnull=True)
    if filter_no_summary:
        consultations = consultations.filter(summary__isnull=True)

    return render(request, "core/doctor/doctor_profile.html", {
        "doctor": doctor,
        "consultations": consultations,
        "filter_no_video": filter_no_video,
        "filter_no_summary": filter_no_summary
    })

# 📌 Редактирование профиля врача
@login_required
def edit_doctor_profile(request):
    doctor = get_object_or_404(Doctor, user=request.user)

    if request.method == "POST":
        form = DoctorProfileForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль обновлён!")
            return redirect("doctor_profile")
    else:
        form = DoctorProfileForm(instance=doctor)

    return render(request, "core/doctor/edit_doctor_profile.html", {"form": form})


def duty_doctors(request):
    doctors = Doctor.objects.filter(is_duty=True)
    return render(request, "core/doctor/doctors.html", {"doctors": doctors})
@login_required
def clinic_doctors(request):
    if request.user.role != "clinic":
        return redirect("home")

    clinic = Clinic.objects.get(user=request.user)
    doctors = Doctor.objects.filter(clinic=clinic)

    return render(request, "core/clinics/clinic_doctors.html", {"doctors": doctors})