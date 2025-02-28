from django.urls import path
from .views import *

urlpatterns = [
    path("", home, name="home"),

    # 🔑 Аутентификация
    path("register/", register, name="register"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),

    # 🏥 Клиники и врачи
    path("clinics/", clinic_list, name="clinic_list"),
    path("doctors/", doctor_list, name="doctor_list"),
    path("doctorsduty/", duty_doctors, name="duty_doctors"),
    path("specialties/", specialties_list, name="specialties_list"),
    path("specialty/<int:specialty_id>/", doctors_by_specialty, name="doctors_by_specialty"),

    # 🗓️ Расписание врача
    path("doctor/<int:doctor_id>/schedule/", doctor_schedule, name="doctor_schedule"),
    path("schedule/create/", create_schedule, name="create_schedule"),
    path("schedule/view/", view_schedule, name="view_schedule"),
    path("schedule/edit/<int:schedule_id>/", edit_schedule, name="edit_schedule"),
    path('schedule/delete/<int:schedule_id>/', delete_schedule, name='delete_schedule'),
    path('schedule/edit/<int:schedule_id>/', edit_schedule, name="edit_schedule"),
    path("schedule/video/<int:schedule_id>/", add_video_link, name="add_video_link"),
    path("schedule/summary/<int:schedule_id>/", add_consultation_summary, name="add_consultation_summary"),
    path("doctor/<int:doctor_id>/schedule/times/", get_schedule_by_date, name="get_schedule_by_date"),
    # 📌 Запись на приём
    path("appointment/book/<int:schedule_id>/", book_appointment, name="book_appointment"),
    path("consent/", consent_view, name="consent_page"),
    path("appointment/success/<int:consultation_id>/", appointment_success, name="appointment_success"),
    path("doctor/schedule/times/", get_doctor_schedule_by_date, name="get_doctor_schedule_by_date"),
    path("schedule/delete/<int:schedule_id>/", delete_schedule_slot, name="delete_schedule_slot"),

    # Удаление всех слотов за один день
    path("schedule/delete/day/<str:date>/", delete_schedule_day, name="delete_schedule_day"),

    path("schedule/create-next-month/", create_next_month_schedule, name="create_schedule_next_month"),
    # 👥 Пациент просматривает консультации
    path("consultations/", patient_consultations, name="patient_consultations"),
    path("clinic/register/", register_clinic, name="register_clinic"),

    path("clinic/profile/", clinic_profile, name="clinic_profile"),

    path("clinic/<int:clinic_id>/", clinic_detail, name="clinic_detail"),

    path("clinic/doctors/", clinic_doctors, name="clinic_doctors"),
    path("clinic/dashboard/", clinic_dashboard, name="clinic_dashboard"),
    path("clinic/add-doctor/", add_doctor, name="add_doctor"),
    path("clinic/edit-doctor/<int:doctor_id>/", edit_doctor, name="edit_doctor"),  # 🔹 Изменение врача
    path("clinic/delete-doctor/<int:doctor_id>/", delete_doctor, name="delete_doctor"),  # 🔹 Удаление врача

    path("specialty/<int:specialty_id>/doctors/", doctors_by_specialty, name="doctors_by_specialty"),

    path("trainings/create/", create_training, name="create_training"),
    path("trainings/", trainings_list, name="trainings_list"),
    path("trainings/join/<int:training_id>/", join_training, name="join_training"),

    path("doctor/profile/", doctor_profile, name="doctor_profile"),
    path("profile/", patient_profile, name="patient_profile"),
    path("patient/<int:patient_id>/", doctor_patient_profile, name="doctor_patient_profile"),
    path("profile/history/", consultation_history, name="consultation_history"),
path("doctor/consultations/history/", doctor_consultation_history, name="doctor_consultation_history"),

    path("profile/edit/", edit_doctor_profile, name="edit_doctor_profile"),

    path("consultation/<int:consultation_id>/add_review/", add_review, name="add_review"),
]
