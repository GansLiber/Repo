from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from .models import TimeSlot, Lesson, TutorSchedule, LessonPhoto
from .forms import CustomLoginForm, TimeSlotForm, BookSlotForm
from django.core.exceptions import ValidationError
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
import calendar

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
    # Получаем все слоты
    slots = TimeSlot.objects.filter(
        tutor=request.user
    ).order_by('datetime')
    
    lessons = Lesson.objects.filter(
        time_slot__tutor=request.user
    ).order_by('time_slot__datetime')
    
    context = {
        'slots': slots,
        'lessons': lessons,
        'upcoming_slots': slots.filter(datetime__gte=timezone.now()),
        'past_lessons': lessons.filter(time_slot__datetime__lt=timezone.now()).order_by('-time_slot__datetime'),
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
        student=request.user
    ).order_by('time_slot__datetime')
    
    context = {
        'available_slots': available_slots,
        'my_lessons': my_lessons,
        'upcoming_lessons': my_lessons.filter(time_slot__datetime__gte=timezone.now()),
        'past_lessons': my_lessons.filter(time_slot__datetime__lt=timezone.now()).order_by('-time_slot__datetime'),
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
            
            # Обновляем слот
            slot.status = 'booked'
            slot.student = request.user
            slot.tutor = slot.tutor  # Сохраняем существующего преподавателя
            slot.save()
            
            messages.success(request, 'Слот успешно забронирован!')
            return redirect('student_dashboard')
    else:
        form = BookSlotForm()
    
    return render(request, 'scheduler/book_slot.html', {
        'form': form,
        'slot': slot
    })

@login_required
@user_passes_test(is_tutor)
def student_list(request):
    # Получаем всех учеников преподавателя
    students = User.objects.filter(
        booked_slots__tutor=request.user
    ).distinct().order_by('first_name', 'last_name')
    
    # Для каждого ученика получаем статистику
    student_stats = []
    for student in students:
        lessons = Lesson.objects.filter(
            student=student,
            time_slot__tutor=request.user
        )
        total_lessons = lessons.count()
        completed_lessons = lessons.filter(status='completed').count()
        upcoming_lessons = lessons.filter(time_slot__datetime__gte=timezone.now()).count()
        
        student_stats.append({
            'student': student,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'upcoming_lessons': upcoming_lessons,
            'last_lesson': lessons.order_by('-time_slot__datetime').first()
        })
    
    return render(request, 'scheduler/student_list.html', {
        'student_stats': student_stats
    })

@login_required
@user_passes_test(is_tutor)
def student_detail(request, student_id):
    student = get_object_or_404(User, id=student_id)
    
    # Получаем все занятия ученика
    lessons = Lesson.objects.filter(
        student=student,
        time_slot__tutor=request.user
    ).order_by('-time_slot__datetime')
    
    # Разделяем на предстоящие и прошедшие
    upcoming_lessons = lessons.filter(time_slot__datetime__gte=timezone.now())
    past_lessons = lessons.filter(time_slot__datetime__lt=timezone.now())
    
    # Статистика
    total_lessons = lessons.count()
    completed_lessons = lessons.filter(status='completed').count()
    cancelled_lessons = lessons.filter(status='cancelled').count()
    
    return render(request, 'scheduler/student_detail.html', {
        'student': student,
        'upcoming_lessons': upcoming_lessons,
        'past_lessons': past_lessons,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'cancelled_lessons': cancelled_lessons
    })

class TutorCalendarView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'scheduler/tutor_calendar.html'

    def test_func(self):
        return self.request.user.groups.filter(name='Tutors').exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем текущую дату или дату из параметров
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))
        
        # Создаем календарь
        cal = calendar.monthcalendar(year, month)
        
        # Получаем все занятия на этот месяц
        start_date = timezone.make_aware(datetime(year, month, 1))
        if month == 12:
            end_date = timezone.make_aware(datetime(year + 1, 1, 1))
        else:
            end_date = timezone.make_aware(datetime(year, month + 1, 1))
            
        lessons = Lesson.objects.filter(
            time_slot__datetime__gte=start_date,
            time_slot__datetime__lt=end_date,
            time_slot__tutor=self.request.user
        ).select_related('student', 'time_slot')
        
        # Создаем словарь занятий по дням
        lessons_by_day = {}
        for lesson in lessons:
            day = lesson.time_slot.datetime.day
            if day not in lessons_by_day:
                lessons_by_day[day] = []
            lessons_by_day[day].append(lesson)
        
        # Добавляем данные в контекст
        today = timezone.localtime(timezone.now())
        context.update({
            'calendar': cal,
            'lessons_by_day': lessons_by_day,
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'prev_month': (month - 1) if month > 1 else 12,
            'prev_year': year if month > 1 else year - 1,
            'next_month': (month + 1) if month < 12 else 1,
            'next_year': year if month < 12 else year + 1,
            'day_names': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
            'today_day': today.day,
            'today_month': today.month,
            'today_year': today.year,
        })
        
        return context
