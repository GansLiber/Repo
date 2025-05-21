from django.test import TestCase
from django.urls import reverse, resolve
from scheduler import views

class UrlsTest(TestCase):
    def test_tutor_dashboard_url(self):
        """Тест URL панели управления тьютора"""
        url = reverse('tutor_dashboard')
        self.assertEqual(url, '/tutor/')
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.tutor_dashboard)

    def test_student_dashboard_url(self):
        """Тест URL панели управления студента"""
        url = reverse('student_dashboard')
        self.assertEqual(url, '/student/')
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.student_dashboard)

    def test_create_time_slot_url(self):
        """Тест URL создания временного слота"""
        url = reverse('create_time_slot')
        self.assertEqual(url, '/tutor/create-slot/')
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.create_time_slot)

    def test_book_slot_url(self):
        """Тест URL бронирования временного слота"""
        url = reverse('book_slot', args=[1])  # 1 - пример ID слота
        self.assertEqual(url, '/student/book-slot/1/')
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.book_slot)

    def test_recurring_templates_list_url(self):
        """Тест URL списка шаблонов регулярных уроков"""
        url = reverse('recurring_templates_list')
        self.assertEqual(url, '/tutor/recurring-templates/')
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.recurring_templates_list)

    def test_recurring_template_create_url(self):
        """Тест URL создания шаблона регулярного урока"""
        url = reverse('recurring_template_create')
        self.assertEqual(url, '/tutor/recurring-templates/create/')
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.recurring_template_create) 