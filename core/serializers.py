from rest_framework import serializers
from .models import Doctor, Patient, Clinic, Consultation, PatientDocument, DoctorSchedule


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'

class PatientDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientDocument
        fields = '__all__'

class PatientSerializer(serializers.ModelSerializer):
    documents = PatientDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Patient
        fields = '__all__'

class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = '__all__'

class ConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = '__all__'


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = ('doctor', 'patient', 'date', 'notes')

    def validate(self, data):
        # Проверка, что слот доступен
        doctor = data['doctor']
        date = data['date']

        slot = DoctorSchedule.objects.filter(
            doctor=doctor,
            date=date.date(),
            start_time=date.time(),
            is_booked=False
        ).first()

        if not slot:
            raise serializers.ValidationError("Выбранное время уже занято или не доступно.")

        return data

    def create(self, validated_data):
        # Бронируем слот
        doctor = validated_data['doctor']
        date = validated_data['date']

        slot = DoctorSchedule.objects.filter(
            doctor=doctor,
            date=date.date(),
            start_time=date.time()
        ).first()

        slot.is_booked = True
        slot.save()

        return super().create(validated_data)
