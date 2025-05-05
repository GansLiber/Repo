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
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('tutor/create-slot/', views.create_time_slot, name='create_time_slot'),
    path('student/book-slot/<int:slot_id>/', views.book_slot, name='book_slot'),
]
