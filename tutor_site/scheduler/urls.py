from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='scheduler/password_change.html',
        success_url='/password_change/done/'
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='scheduler/password_change_done.html'
    ), name='password_change_done'),
    path('tutor/', views.tutor_dashboard, name='tutor_dashboard'),
    path('tutor/students/', views.student_list, name='student_list'),
    path('tutor/students/<int:student_id>/', views.student_detail, name='student_detail'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('tutor/create-slot/', views.create_time_slot, name='create_time_slot'),
    path('student/book-slot/<int:slot_id>/', views.book_slot, name='book_slot'),
    path('tutor/calendar/', views.TutorCalendarView.as_view(), name='tutor_calendar'),
    path('student/cancel-lesson/<int:lesson_id>/', views.cancel_lesson, name='cancel_lesson'),
    path('tutor/recurring-templates/', views.recurring_templates_list, name='recurring_templates_list'),
    path('tutor/recurring-templates/create/', views.recurring_template_create, name='recurring_template_create'),
    path('tutor/recurring-templates/<int:template_id>/edit/', views.recurring_template_edit, name='recurring_template_edit'),
]
