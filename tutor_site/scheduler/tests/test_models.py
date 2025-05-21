from django.test import TestCase
from django.contrib.auth.models import User, Group
from scheduler.models import TimeSlot, Lesson, RecurringLessonTemplate, TutorSchedule
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

class TimeSlotModelTest(TestCase):
    def setUp(self):
        # Создаем пользователей для тестов
        self.tutor = User.objects.create_user(
            username='test_tutor',
            password='testpass123',
            email='tutor@test.com'
        )
        
        self.student = User.objects.create_user(
            username='test_student',
            password='testpass123',
            email='student@test.com'
        )
        
        # Создаем временной слот
        self.time_slot = TimeSlot.objects.create(
            tutor=self.tutor,
            datetime=timezone.now() + timedelta(days=1),
            duration=60,
            status='available'
        )

    def test_time_slot_creation(self):
        """Тест создания временного слота"""
        self.assertEqual(self.time_slot.tutor, self.tutor)
        self.assertEqual(self.time_slot.duration, 60)
        self.assertEqual(self.time_slot.status, 'available')
        self.assertIsNone(self.time_slot.student)

    def test_time_slot_str_method(self):
        """Тест строкового представления временного слота"""
        expected_str = f"{self.tutor.username} - {self.time_slot.datetime} (available)"
        self.assertEqual(str(self.time_slot), expected_str)

    def test_overlapping_time_slots(self):
        """Тест на проверку пересечения временных слотов"""
        with self.assertRaises(ValidationError):
            # Пытаемся создать слот в то же время
            TimeSlot.objects.create(
                tutor=self.tutor,
                datetime=self.time_slot.datetime,
                duration=60,
                status='available'
            )

class LessonModelTest(TestCase):
    def setUp(self):
        # Создаем пользователей
        self.tutor = User.objects.create_user(username='tutor', password='pass123')
        self.student = User.objects.create_user(username='student', password='pass123')
        
        # Создаем временной слот
        self.time_slot = TimeSlot.objects.create(
            tutor=self.tutor,
            datetime=timezone.now() + timedelta(days=1),
            duration=60,
            status='available'
        )
        
        # Создаем урок
        self.lesson = Lesson.objects.create(
            time_slot=self.time_slot,
            student=self.student,
            subject='math',
            status='scheduled'
        )

    def test_lesson_creation(self):
        """Тест создания урока"""
        self.assertEqual(self.lesson.time_slot, self.time_slot)
        self.assertEqual(self.lesson.student, self.student)
        self.assertEqual(self.lesson.subject, 'math')
        self.assertEqual(self.lesson.status, 'scheduled')

    def test_lesson_str_method(self):
        """Тест строкового представления урока"""
        expected_str = f"{self.student.username} - {self.time_slot.datetime} (scheduled)"
        self.assertEqual(str(self.lesson), expected_str)

class TutorScheduleModelTest(TestCase):
    def setUp(self):
        self.tutor = User.objects.create_user(username='tutor', password='pass123')
        
        # Создаем расписание тьютора
        self.schedule = TutorSchedule.objects.create(
            tutor=self.tutor,
            day_of_week='monday',
            start_time='09:00',
            end_time='10:00',
            is_available=True
        )

    def test_schedule_creation(self):
        """Тест создания расписания тьютора"""
        self.assertEqual(self.schedule.tutor, self.tutor)
        self.assertEqual(self.schedule.day_of_week, 'monday')
        self.assertEqual(str(self.schedule.start_time), '09:00')
        self.assertEqual(str(self.schedule.end_time), '10:00')
        self.assertTrue(self.schedule.is_available)

    def test_schedule_str_method(self):
        """Тест строкового представления расписания"""
        expected_str = f"{self.tutor.username} - {self.schedule.get_day_of_week_display()} {self.schedule.start_time}-{self.schedule.end_time}"
        self.assertEqual(str(self.schedule), expected_str)

class RecurringLessonTemplateTest(TestCase):
    def setUp(self):
        # Создаем пользователей
        self.tutor = User.objects.create_user(username='tutor', password='pass123')
        self.student = User.objects.create_user(username='student', password='pass123')
        
        # Создаем шаблон регулярного урока
        self.template = RecurringLessonTemplate.objects.create(
            tutor=self.tutor,
            student=self.student,
            weekday=0,  # Понедельник
            time=timezone.now().time(),
            duration=60,
            subject='math',
            start_date=timezone.now().date()
        )

    def test_template_creation(self):
        """Тест создания шаблона регулярного урока"""
        self.assertEqual(self.template.tutor, self.tutor)
        self.assertEqual(self.template.student, self.student)
        self.assertEqual(self.template.weekday, 0)
        self.assertEqual(self.template.duration, 60)
        self.assertEqual(self.template.subject, 'math')
        self.assertTrue(self.template.is_active)

    def test_template_str_method(self):
        """Тест строкового представления шаблона"""
        expected_str = f"{self.student.username} {self.template.get_weekday_display()} {self.template.time} (math)"
        self.assertEqual(str(self.template), expected_str) 