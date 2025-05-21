from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from scheduler.models import TimeSlot, Lesson, RecurringLessonTemplate
from django.utils import timezone
from datetime import timedelta

class BaseViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Создаем группы
        self.tutor_group = Group.objects.create(name='Tutors')
        self.student_group = Group.objects.create(name='Students')
        
        # Создаем тьютора
        self.tutor = User.objects.create_user(
            username='test_tutor',
            password='testpass123',
            email='tutor@test.com'
        )
        self.tutor.groups.add(self.tutor_group)
        
        # Создаем студента
        self.student = User.objects.create_user(
            username='test_student',
            password='testpass123',
            email='student@test.com'
        )
        self.student.groups.add(self.student_group)

class TutorViewsTest(BaseViewTest):
    def test_tutor_dashboard_view(self):
        """Тест доступа к панели управления тьютора"""
        # Пробуем получить доступ без авторизации
        response = self.client.get(reverse('tutor_dashboard'))
        self.assertEqual(response.status_code, 302)  # Редирект на страницу входа
        
        # Авторизуемся как тьютор
        self.client.login(username='test_tutor', password='testpass123')
        response = self.client.get(reverse('tutor_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'scheduler/tutor/dashboard.html')

    def test_create_time_slot_view(self):
        """Тест создания временного слота"""
        self.client.login(username='test_tutor', password='testpass123')
        
        data = {
            'datetime': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'duration': 60,
            'notes': 'Test slot'
        }
        
        response = self.client.post(reverse('create_time_slot'), data)
        self.assertEqual(response.status_code, 302)  # Редирект после успешного создания
        
        # Проверяем, что слот создан
        self.assertTrue(TimeSlot.objects.filter(tutor=self.tutor).exists())

    def test_recurring_template_create_view(self):
        """Тест создания шаблона регулярного урока"""
        self.client.login(username='test_tutor', password='testpass123')
        
        data = {
            'student': self.student.id,
            'weekday': 0,
            'time': '14:00',
            'duration': 60,
            'subject': 'math',
            'start_date': timezone.now().date(),
            'is_active': True
        }
        
        response = self.client.post(reverse('recurring_template_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(RecurringLessonTemplate.objects.filter(tutor=self.tutor).exists())

class StudentViewsTest(BaseViewTest):
    def setUp(self):
        super().setUp()
        # Создаем временной слот для тестов
        self.time_slot = TimeSlot.objects.create(
            tutor=self.tutor,
            datetime=timezone.now() + timedelta(days=1),
            duration=60,
            status='available'
        )

    def test_student_dashboard_view(self):
        """Тест доступа к панели управления студента"""
        # Пробуем получить доступ без авторизации
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 302)  # Редирект на страницу входа
        
        # Авторизуемся как студент
        self.client.login(username='test_student', password='testpass123')
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'scheduler/student/dashboard.html')

    def test_book_slot_view(self):
        """Тест бронирования временного слота"""
        self.client.login(username='test_student', password='testpass123')
        
        data = {
            'subject': 'math',
            'notes': 'Test booking'
        }
        
        response = self.client.post(
            reverse('book_slot', args=[self.time_slot.id]),
            data
        )
        self.assertEqual(response.status_code, 302)  # Редирект после успешного бронирования
        
        # Проверяем, что слот забронирован
        self.time_slot.refresh_from_db()
        self.assertEqual(self.time_slot.status, 'booked')
        
        # Проверяем, что урок создан
        self.assertTrue(
            Lesson.objects.filter(
                time_slot=self.time_slot,
                student=self.student
            ).exists()
        ) 