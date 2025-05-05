from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('tutor/', views.tutor_dashboard, name='tutor_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('tutor/create-slot/', views.create_time_slot, name='create_time_slot'),
    path('student/book-slot/<int:slot_id>/', views.book_slot, name='book_slot'),
]
