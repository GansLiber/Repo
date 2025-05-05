from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import TimeSlot, Lesson, TutorSchedule, LessonPhoto
from .forms import CustomLoginForm, TimeSlotForm, BookSlotForm
from django.core.exceptions import ValidationError

class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'scheduler/login.html'

    def form_valid(self, form):
        user = form.get_user()
        if not user.groups.exists():
            messages.error(self.request, 'У вас нет прав доступа. Обратитесь к администратору.')
            return render(self.request, 'scheduler/login.html', {
                'form': form,
                'error': 'У вас нет прав доступа. Обратитесь к администратору.'
            })
        messages.success(self.request, f'Добро пожаловать, {user.username}!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Неверное имя пользователя или пароль.')
        return super().form_invalid(form)

def is_tutor(user):
    return user.groups.filter(name='Tutors').exists()

def is_student(user):
    return user.groups.filter(name='Students').exists()

def home_view(request):
    if request.user.is_authenticated:
        if is_tutor(request.user):
            return redirect('tutor_dashboard')
        elif is_student(request.user):
            return redirect('student_dashboard')
    return render(request, 'scheduler/home.html')

@login_required
@user_passes_test(is_tutor)
def tutor_dashboard(request):
    # Получаем слоты на ближайшие 7 дней
    start_date = timezone.now()
    end_date = start_date + timedelta(days=7)
    
    slots = TimeSlot.objects.filter(
        tutor=request.user,
        datetime__range=[start_date, end_date]
    ).order_by('datetime')
    
    lessons = Lesson.objects.filter(
        time_slot__tutor=request.user,
        time_slot__datetime__range=[start_date, end_date]
    ).order_by('time_slot__datetime')
    
    context = {
        'slots': slots,
        'lessons': lessons,
        'upcoming_slots': slots.filter(datetime__gte=timezone.now()),
        'past_lessons': lessons.filter(time_slot__datetime__lt=timezone.now()),
    }
    return render(request, 'scheduler/tutor_dashboard.html', context)

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    # Получаем слоты на ближайшие 7 дней
    start_date = timezone.now()
    end_date = start_date + timedelta(days=7)
    
    available_slots = TimeSlot.objects.filter(
        status='available',
        datetime__range=[start_date, end_date]
    ).order_by('datetime')
    
    my_lessons = Lesson.objects.filter(
        student=request.user,
        time_slot__datetime__range=[start_date, end_date]
    ).order_by('time_slot__datetime')
    
    context = {
        'available_slots': available_slots,
        'my_lessons': my_lessons,
        'upcoming_lessons': my_lessons.filter(time_slot__datetime__gte=timezone.now()),
        'past_lessons': my_lessons.filter(time_slot__datetime__lt=timezone.now()),
    }
    return render(request, 'scheduler/student_dashboard.html', context)

@login_required
@user_passes_test(is_tutor)
def create_time_slot(request):
    if request.method == 'POST':
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            try:
                time_slot = form.save(commit=False)
                time_slot.tutor = request.user
                time_slot.full_clean()  # Проверяем валидацию после установки tutor
                time_slot.save()
                messages.success(request, 'Слот успешно создан!')
                return redirect('tutor_dashboard')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = TimeSlotForm()
    return render(request, 'scheduler/create_time_slot.html', {'form': form})

@login_required
@user_passes_test(is_student)
def book_slot(request, slot_id):
    slot = get_object_or_404(TimeSlot, id=slot_id, status='available')
    
    # Проверяем, не существует ли уже урок для этого слота
    if hasattr(slot, 'lesson'):
        messages.error(request, 'Этот слот уже забронирован.')
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        form = BookSlotForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.time_slot = slot
            lesson.student = request.user
            lesson.save()
            
            # Обработка фото
            photos = request.FILES.getlist('photos')
            for photo in photos:
                LessonPhoto.objects.create(
                    lesson=lesson,
                    photo=photo
                )
            
            slot.status = 'booked'
            slot.student = request.user
            slot.save()
            
            messages.success(request, 'Слот успешно забронирован!')
            return redirect('student_dashboard')
    else:
        form = BookSlotForm()
    
    return render(request, 'scheduler/book_slot.html', {
        'form': form,
        'slot': slot
    })
