from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from scheduler.forms import TimeSlotForm, BookSlotForm, RecurringLessonTemplateForm, CustomLoginForm
from django.contrib.auth.models import User

class TimeSlotFormTest(TestCase):
    def setUp(self):
        self.valid_data = {
            'datetime': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'duration': 60,
            'notes': 'Test lesson'
        }

    def test_valid_time_slot_form(self):
        """Тест валидной формы временного слота"""
        form = TimeSlotForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_invalid_duration(self):
        """Тест невалидной длительности занятия"""
        data = self.valid_data.copy()
        data['duration'] = 0  # Нулевая длительность
        
        form = TimeSlotForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('duration', form.errors)

class BookSlotFormTest(TestCase):
    def setUp(self):
        self.valid_data = {
            'subject': 'math',
            'notes': 'Test booking notes'
        }

    def test_valid_book_slot_form(self):
        """Тест валидной формы бронирования"""
        form = BookSlotForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_invalid_subject(self):
        """Тест невалидного предмета"""
        data = self.valid_data.copy()
        data['subject'] = 'invalid_subject'
        
        form = BookSlotForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('subject', form.errors)

class RecurringLessonTemplateFormTest(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username='test_student', password='pass123')
        
        self.valid_data = {
            'student': self.student.id,
            'weekday': 0,  # Понедельник
            'time': '14:00',
            'duration': 60,
            'subject': 'math',
            'start_date': timezone.now().date(),
            'is_active': True
        }

    def test_valid_template_form(self):
        """Тест валидной формы шаблона регулярного урока"""
        form = RecurringLessonTemplateForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_invalid_weekday(self):
        """Тест невалидного дня недели"""
        data = self.valid_data.copy()
        data['weekday'] = 7  # Невалидный день недели
        
        form = RecurringLessonTemplateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('weekday', form.errors)

class CustomLoginFormTest(TestCase):
    def test_form_has_correct_fields(self):
        """Тест наличия нужных полей в форме входа"""
        form = CustomLoginForm()
        self.assertIn('username', form.fields)
        self.assertIn('password', form.fields)
        
        # Проверяем атрибуты полей
        self.assertEqual(
            form.fields['username'].widget.attrs['placeholder'],
            'Имя пользователя'
        )
        self.assertEqual(
            form.fields['password'].widget.attrs['placeholder'],
            'Пароль'
        ) 