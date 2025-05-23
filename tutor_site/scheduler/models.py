from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
from django.utils import timezone
from PIL import Image
import os
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    telegram = models.CharField(max_length=100, blank=True, null=True, help_text='Telegram username')

    def __str__(self):
        return f"Profile of {self.user.username}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    elif not UserProfile.objects.filter(user=instance).exists():
        UserProfile.objects.create(user=instance)

class ResourceLink(models.Model):
    CATEGORY_CHOICES = [
        ('textbook', 'Учебник'),
        ('formulas', 'Формулы'),
        ('whiteboard', 'Онлайн доска'),
        ('other', 'Другое'),
    ]
    
    title = models.CharField(max_length=200)
    url = models.URLField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_resources')
    shared_with = models.ManyToManyField(User, related_name='available_resources', blank=True)

    def __str__(self):
        return self.title

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
        day_map = dict(self.DAYS_OF_WEEK)
        return day_map[self.day_of_week]

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

    class Meta:
        unique_together = ['tutor', 'datetime']
        ordering = ['datetime']

    def clean(self):
        # Проверяем, нет ли пересечений по времени с другими слотами
        if self.datetime and self.duration and self.tutor_id:
            slot_start = self.datetime
            slot_end = self.datetime + timedelta(minutes=self.duration)
            
            # Проверяем пересечения с существующими слотами
            overlapping_slots = TimeSlot.objects.filter(
                tutor_id=self.tutor_id,
                datetime__lt=slot_end,  # Начало существующего слота раньше конца нового
            ).filter(
                datetime__gte=slot_start - timedelta(minutes=self.duration)  # Конец существующего слота позже начала нового
            )
            
            if self.pk:
                overlapping_slots = overlapping_slots.exclude(pk=self.pk)
                
            if overlapping_slots.exists():
                raise ValidationError('Это время пересекается с другим занятием. Учитывайте длительность занятий.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tutor.username} - {self.datetime} ({self.status})"

def lesson_photo_path(instance, filename):
    # Путь для сохранения: lesson_photos/YYYY/MM/DD/filename
    return os.path.join('lesson_photos', timezone.now().strftime('%Y/%m/%d'), filename)

class LessonPhoto(models.Model):
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to=lesson_photo_path)
    thumbnail = models.ImageField(upload_to=lesson_photo_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.photo and not self.thumbnail:
            # Создаем миниатюру
            img = Image.open(self.photo.path)
            
            # Определяем размеры для миниатюры
            thumbnail_size = (150, 150)
            
            # Сохраняем пропорции
            img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            
            # Формируем имя файла для миниатюры
            filename, ext = os.path.splitext(os.path.basename(self.photo.name))
            thumbnail_name = f"{filename}_thumb{ext}"
            thumbnail_path = os.path.join(os.path.dirname(self.photo.path), thumbnail_name)
            
            # Сохраняем миниатюру
            img.save(thumbnail_path)
            
            # Обновляем поле thumbnail
            self.thumbnail = os.path.join(os.path.dirname(self.photo.name), thumbnail_name)
            super().save(update_fields=['thumbnail'])

    def __str__(self):
        return f"Photo for lesson {self.lesson.id}"

class Lesson(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Запланировано'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]

    SUBJECT_CHOICES = [
        ('math', 'Математика'),
        ('physics', 'Физика'),
        ('chemistry', 'Химия'),
        ('biology', 'Биология'),
        ('english', 'Английский язык'),
        ('russian', 'Русский язык'),
        ('literature', 'Литература'),
        ('history', 'История'),
        ('geography', 'География'),
        ('other', 'Другое'),
    ]

    time_slot = models.OneToOneField(TimeSlot, on_delete=models.CASCADE, related_name='lesson')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booked_lessons')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='math')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.username} - {self.time_slot.datetime} ({self.status})"

class RecurringLessonTemplate(models.Model):
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recurring_templates_as_tutor')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recurring_templates_as_student')
    weekday = models.IntegerField(choices=[(i, day) for i, day in enumerate(['Пн','Вт','Ср','Чт','Пт','Сб','Вс'])])
    time = models.TimeField()
    duration = models.IntegerField(default=60)
    subject = models.CharField(max_length=20, choices=Lesson.SUBJECT_CHOICES, default='math')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} {self.get_weekday_display()} {self.time} ({self.subject})"

class TutorStudent(models.Model):
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='students_list')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tutors_list')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    subjects = models.JSONField(default=list, help_text='Список предметов, которые преподаёт')

    class Meta:
        unique_together = ['tutor', 'student']
        verbose_name = 'Связь преподаватель-ученик'
        verbose_name_plural = 'Связи преподаватель-ученик'

    def __str__(self):
        return f"{self.tutor.get_full_name()} - {self.student.get_full_name()}"
