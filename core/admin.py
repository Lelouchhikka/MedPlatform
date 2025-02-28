from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Doctor, Consultation, Patient, Clinic, Specialty, DoctorSchedule, User


class DoctorAdmin(admin.ModelAdmin):
    list_display = ("user", "get_specialty", "clinic", "phone", "rating")
    list_filter = ( "clinic",)

    def get_specialty(self, obj):
        return ", ".join([s.name for s in obj.specialties.all()])

    get_specialty.short_description = "Мамандығы"


class ConsultationAdmin(admin.ModelAdmin):
    list_display = ("doctor", "patient", "get_date", "video_link", "get_summary")
    list_filter = ("doctor", "patient", "schedule__date")

    def get_date(self, obj):
        return obj.schedule.date
    get_date.short_description = "Дата"

    def get_summary(self, obj):
        return obj.summary if obj.summary else "Нет данных"
    get_summary.short_description = "Итоги консультации"


class PatientAdmin(admin.ModelAdmin):
    list_display = ("user", "iin", "phone")
    list_filter = ("iin",)


class ClinicAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "rating")
    list_filter = ("city",)


class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ("name",)
    list_filter = ("name",)


class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ("doctor", "date", "start_time", "end_time", "is_booked")
    list_filter = ("doctor", "date")
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff', 'is_superuser')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email')

# Регистрируем модели
admin.site.register(Doctor, DoctorAdmin)
admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(Clinic, ClinicAdmin)
admin.site.register(Specialty, SpecialtyAdmin)
admin.site.register(DoctorSchedule, DoctorScheduleAdmin)
