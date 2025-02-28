from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime, timedelta
from .models import Doctor, DoctorSchedule

@receiver(post_save, sender=Doctor)
def create_doctor_schedule(sender, instance, created, **kwargs):
    if created:
        today = datetime.today().date()
        for i in range(14):  # Создаем расписание на 2 недели вперед
            date = today + timedelta(days=i)
            if date.weekday() < 5:  # Только будни (0=понедельник, 4=пятница)
                for hour in range(9, 18):  # С 9 до 18 по 1 часу
                    DoctorSchedule.objects.create(
                        doctor=instance,
                        date=date,
                        start_time=f"{hour}:00",
                        end_time=f"{hour+1}:00"
                    )
