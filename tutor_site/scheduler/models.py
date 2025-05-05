from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
from django.utils import timezone

User = get_user_model()

class TutorSchedule(models.Model):
    DAYS_OF_WEEK = [
        ('monday', 'Понедельник'),
        ('tuesday', 'Вторник'),
        ('wednesday', 'Среда'),
        ('thursday', 'Четверг'),
        ('friday', 'Пятница'),
        ('saturday', 'Суббота'),
        ('sunday', 'Воскресенье'),
    ]

    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tutor_schedules')
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.tutor.username} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

    def get_day_of_week_display(self):
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        return days[self.day_of_week]

class TimeSlot(models.Model):
    STATUS_CHOICES = [
        ('available', 'Доступно'),
        ('booked', 'Забронировано'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]

    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_slots')
    student = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='booked_slots')
    datetime = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    duration = models.IntegerField(default=60, help_text='Длительность в минутах')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.tutor.username} - {self.datetime} ({self.status})"

class Lesson(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Запланировано'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]

    time_slot = models.OneToOneField(TimeSlot, on_delete=models.CASCADE, related_name='lesson')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lessons')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='scheduled')
    homework = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.time_slot.datetime} ({self.status})"
