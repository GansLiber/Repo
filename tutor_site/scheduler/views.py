from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.utils import timezone, translation
from datetime import datetime, timedelta
from .models import TimeSlot, Lesson, TutorSchedule, LessonPhoto, RecurringLessonTemplate, ResourceLink, TutorStudent
from .forms import CustomLoginForm, TimeSlotForm, BookSlotForm, RecurringLessonTemplateForm, LessonPhotosForm
from django.core.exceptions import ValidationError
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
import calendar
import os
from django.contrib.auth import login

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
    
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if is_tutor(user):
                return redirect('tutor_dashboard')
            elif is_student(user):
                return redirect('student_dashboard')
    else:
        form = CustomLoginForm()
    
    return render(request, 'scheduler/login.html', {'form': form})

@login_required
@user_passes_test(is_tutor)
def tutor_dashboard(request):
    ensure_recurring_slots_for_tutor(request.user)
    # Получаем все слоты
    slots = TimeSlot.objects.filter(
        tutor=request.user
    ).order_by('datetime')
    
    lessons = Lesson.objects.filter(
        time_slot__tutor=request.user
    ).order_by('time_slot__datetime')
    
    cancelled_lessons = lessons.filter(status='cancelled')
    
    context = {
        'now': timezone.now(),
        'slots': slots,
        'lessons': lessons,
        'upcoming_slots': slots.filter(datetime__gte=timezone.now()),
        'past_lessons': lessons.filter(time_slot__datetime__lt=timezone.now()).order_by('-time_slot__datetime'),
        'cancelled_lessons': cancelled_lessons,
    }
    return render(request, 'scheduler/tutor/dashboard.html', context)

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    # Получаем слоты на ближайшие 7 дней
    start_date = timezone.now()
    end_date = start_date + timedelta(days=7)
    
    # Получаем активных преподавателей студента
    my_tutors = User.objects.filter(
        students_list__student=request.user,
        students_list__is_active=True
    )
    
    # Если у студента нет преподавателей
    if not my_tutors.exists():
        messages.info(request, 'У вас пока нет преподавателей. Дождитесь, пока преподаватель добавит вас к себе.')
        available_slots = TimeSlot.objects.none()
    else:
        # Получаем доступные слоты только от преподавателей студента
        available_slots = TimeSlot.objects.filter(
            status='available',
            datetime__range=[start_date, end_date],
            tutor__in=my_tutors
        ).order_by('datetime')
    
    my_lessons = Lesson.objects.filter(
        student=request.user
    ).order_by('time_slot__datetime')
    
    context = {
        'now': timezone.now(),
        'available_slots': available_slots,
        'my_lessons': my_lessons,
        'upcoming_lessons': my_lessons.filter(time_slot__datetime__gte=timezone.now()),
        'past_lessons': my_lessons.filter(time_slot__datetime__lt=timezone.now()).order_by('-time_slot__datetime'),
        'my_tutors': my_tutors,  # Добавляем список преподавателей в контекст
    }
    return render(request, 'scheduler/student/dashboard.html', context)

@login_required
@user_passes_test(is_student)
def student_profile(request):
    # Получаем все занятия ученика
    lessons = Lesson.objects.filter(
        student=request.user
    ).order_by('-time_slot__datetime')
    
    if request.method == 'POST' and request.POST.get('action') == 'add_link':
        # Проверяем, что запрос от преподавателя
        is_tutor_view = request.user.groups.filter(name='Tutors').exists()
        if is_tutor_view:
            try:
                # Получаем ID ученика из URL
                student_id = request.GET.get('student_id')
                student = get_object_or_404(User, id=student_id)
                ResourceLink.objects.create(
                    title=request.POST['title'],
                    url=request.POST['url'],
                    description=request.POST.get('description', ''),
                    category=request.POST['category'],
                    created_by=request.user
                )
                link = ResourceLink.objects.get(id=request.POST['link_id'])
                link.shared_with.add(student)
                messages.success(request, 'Ссылка успешно добавлена!')
            except Exception as e:
                messages.error(request, f'Ошибка при добавлении ссылки: {str(e)}')
        else:
            messages.error(request, 'У вас нет прав для добавления ссылок')
        return redirect('student_profile')
    
    # Разделяем на предстоящие и прошедшие
    upcoming_lessons = lessons.filter(time_slot__datetime__gte=timezone.now())
    past_lessons = lessons.filter(time_slot__datetime__lt=timezone.now())
    
    # Статистика
    total_lessons = lessons.count()
    completed_lessons = lessons.filter(status='completed').count()
    cancelled_lessons = lessons.filter(status='cancelled').count()
    
    # Статистика по предметам
    subjects_stats = {}
    for lesson in lessons:
        subject = lesson.get_subject_display()
        if subject not in subjects_stats:
            subjects_stats[subject] = 0
        subjects_stats[subject] += 1
    
    # Получаем преподавателей через TutorStudent
    tutor_relations = TutorStudent.objects.filter(
        student=request.user,
        is_active=True
    ).select_related('tutor', 'tutor__profile')
    
    # Получаем ресурсы, доступные студенту
    resource_links = {}
    for link in ResourceLink.objects.filter(shared_with=request.user).order_by('category', 'title'):
        category = link.get_category_display()
        if category not in resource_links:
            resource_links[category] = []
        resource_links[category].append(link)
    
    return render(request, 'scheduler/student/profile.html', {
        'upcoming_lessons': upcoming_lessons,
        'past_lessons': past_lessons,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'cancelled_lessons': cancelled_lessons,
        'subjects_stats': subjects_stats,
        'tutor_relations': tutor_relations,
        'resource_links': resource_links,
        'is_tutor_view': request.user.groups.filter(name='Tutors').exists(),
        'viewed_user': request.user
    })

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
    return render(request, 'scheduler/tutor/create_time_slot.html', {'form': form})

@login_required
@user_passes_test(is_student)
def book_slot(request, slot_id):
    slot = get_object_or_404(TimeSlot, id=slot_id, status='available')
    # Запретить запись, если до начала слота < 12 часов
    if slot.datetime - timezone.now() < timedelta(hours=12):
        messages.error(request, 'Запись на это занятие уже закрыта (менее чем за 12 часов до начала).')
        return redirect('student_dashboard')
    
    # Проверяем, не существует ли уже урок для этого слота и он не отменён
    if hasattr(slot, 'lesson') and slot.lesson.status != 'cancelled':
        messages.error(request, 'Этот слот уже забронирован.')
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        form = BookSlotForm(request.POST, request.FILES)
        if form.is_valid():
            if hasattr(slot, 'lesson') and slot.lesson.status == 'cancelled':
                # Реанимируем отменённый lesson
                lesson = slot.lesson
                lesson.status = 'scheduled'
                lesson.student = request.user
                lesson.save()
            else:
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
    
    return render(request, 'scheduler/student/book_slot.html', {
        'form': form,
        'slot': slot
    })

@login_required
@user_passes_test(is_tutor)
def student_list(request):
    # Получаем всех активных учеников преподавателя через TutorStudent
    tutor_students = TutorStudent.objects.filter(
        tutor=request.user,
        is_active=True
    ).select_related('student')
    
    # Для каждого ученика получаем статистику
    student_stats = []
    for relation in tutor_students:
        lessons = Lesson.objects.filter(
            student=relation.student,
            time_slot__tutor=request.user
        )
        total_lessons = lessons.count()
        completed_lessons = lessons.filter(status='completed').count()
        upcoming_lessons = lessons.filter(time_slot__datetime__gte=timezone.now()).count()
        
        student_stats.append({
            'student': relation.student,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'upcoming_lessons': upcoming_lessons,
            'last_lesson': lessons.order_by('-time_slot__datetime').first(),
            'subjects': relation.subjects  # Добавляем предметы из связи
        })
    
    return render(request, 'scheduler/tutor/student_list.html', {
        'student_stats': student_stats
    })

@login_required
@user_passes_test(is_tutor)
def student_detail(request, student_id):
    student = get_object_or_404(User, id=student_id)
    
    # Проверяем, есть ли у преподавателя доступ к этому ученику
    if not TutorStudent.objects.filter(tutor=request.user, student=student, is_active=True).exists():
        messages.error(request, 'У вас нет доступа к этому ученику')
        return redirect('student_list')
    
    # Получаем все занятия ученика с этим преподавателем
    lessons = Lesson.objects.filter(
        student=student,
        time_slot__tutor=request.user
    ).order_by('-time_slot__datetime')
    
    if request.method == 'POST' and request.POST.get('action') == 'add_link':
        try:
            link = ResourceLink.objects.create(
                title=request.POST['title'],
                url=request.POST['url'],
                description=request.POST.get('description', ''),
                category=request.POST['category'],
                created_by=request.user
            )
            link.shared_with.add(student)
            messages.success(request, 'Ссылка успешно добавлена!')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении ссылки: {str(e)}')
        return redirect('student_detail', student_id=student_id)
    
    # Разделяем на предстоящие и прошедшие
    upcoming_lessons = lessons.filter(time_slot__datetime__gte=timezone.now())
    past_lessons = lessons.filter(time_slot__datetime__lt=timezone.now())
    
    # Статистика
    total_lessons = lessons.count()
    completed_lessons = lessons.filter(status='completed').count()
    cancelled_lessons = lessons.filter(status='cancelled').count()
    
    # Статистика по предметам
    subjects_stats = {}
    for lesson in lessons:
        subject = lesson.get_subject_display()
        if subject not in subjects_stats:
            subjects_stats[subject] = 0
        subjects_stats[subject] += 1
    
    # Получаем преподавателей через TutorStudent
    tutor_relations = TutorStudent.objects.filter(
        student=student,
        is_active=True
    ).select_related('tutor', 'tutor__profile')
    
    # Получаем ресурсы, доступные студенту
    resource_links = {}
    for link in ResourceLink.objects.filter(shared_with=student).order_by('category', 'title'):
        category = link.get_category_display()
        if category not in resource_links:
            resource_links[category] = []
        resource_links[category].append(link)
    
    return render(request, 'scheduler/student/profile.html', {
        'viewed_user': student,  # Для отображения данных ученика
        'upcoming_lessons': upcoming_lessons,
        'past_lessons': past_lessons,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'cancelled_lessons': cancelled_lessons,
        'subjects_stats': subjects_stats,
        'tutor_relations': tutor_relations,
        'resource_links': resource_links,
        'is_tutor_view': True,
        'viewing_as_tutor': True  # Добавляем флаг для шапки
    })

@login_required
@user_passes_test(is_student)
def cancel_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, student=request.user)
    if lesson.time_slot.datetime - timezone.now() < timedelta(hours=12):
        messages.error(request, 'Отменить занятие можно только за 12 часов до начала.')
        return redirect('student_dashboard')
    if request.method == 'POST':
        reason = request.POST.get('cancel_reason', '').strip()
        lesson.status = 'cancelled'
        lesson.notes = f"[ОТМЕНА СТУДЕНТОМ]: {reason}\n" + lesson.notes
        lesson.save()
        lesson.time_slot.status = 'available'
        lesson.time_slot.student = None
        lesson.time_slot.save()
        messages.success(request, 'Занятие отменено.')
        return redirect('student_dashboard')
    return render(request, 'scheduler/cancel_lesson.html', {'lesson': lesson})

class TutorCalendarView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'scheduler/tutor/calendar.html'

    def test_func(self):
        return self.request.user.groups.filter(name='Tutors').exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))
        cal = calendar.monthcalendar(year, month)
        start_date = timezone.make_aware(datetime(year, month, 1))
        if month == 12:
            end_date = timezone.make_aware(datetime(year + 1, 1, 1))
        else:
            end_date = timezone.make_aware(datetime(year, month + 1, 1))
        lessons = Lesson.objects.filter(
            time_slot__datetime__gte=start_date,
            time_slot__datetime__lt=end_date,
            time_slot__tutor=self.request.user,
            status__in=['scheduled', 'completed']
        ).select_related('student', 'time_slot')
        lessons_by_day = {}
        for lesson in lessons:
            day = lesson.time_slot.datetime.day
            if day not in lessons_by_day:
                lessons_by_day[day] = []
            lessons_by_day[day].append(lesson)
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

def ensure_recurring_slots_for_tutor(tutor):
    today = timezone.localdate()
    week_ahead = today + timedelta(days=7)
    templates = RecurringLessonTemplate.objects.filter(tutor=tutor, is_active=True)
    for template in templates:
        # Для каждого дня в диапазоне
        cur = today
        while cur <= week_ahead:
            if cur >= template.start_date and (not template.end_date or cur <= template.end_date):
                if cur.weekday() == template.weekday:
                    dt = datetime.combine(cur, template.time)
                    dt = timezone.make_aware(dt)
                    # Проверяем, есть ли отменённый lesson на эту дату
                    cancelled_lesson_exists = Lesson.objects.filter(
                        time_slot__tutor=tutor,
                        time_slot__student=template.student,
                        time_slot__datetime=dt,
                        status='cancelled'
                    ).exists()

                    # Проверяем, есть ли уже слот (любого статуса)
                    slot_exists = TimeSlot.objects.filter(
                        tutor=tutor,
                        datetime=dt
                    ).exists()

                    if not slot_exists and not cancelled_lesson_exists:
                        slot = TimeSlot.objects.create(
                            tutor=tutor,
                            student=template.student,
                            datetime=dt,
                            duration=template.duration,
                            status='booked',
                        )
                        lesson = Lesson.objects.create(
                            time_slot=slot,
                            student=template.student,
                            status='scheduled',
                            subject=template.subject
                        )
            cur += timedelta(days=1)

@login_required
@user_passes_test(is_tutor)
def recurring_templates_list(request):
    templates = RecurringLessonTemplate.objects.filter(tutor=request.user)
    return render(request, 'scheduler/tutor/recurring_templates/list.html', {'templates': templates})

@login_required
@user_passes_test(is_tutor)
def recurring_template_create(request):
    if request.method == 'POST':
        form = RecurringLessonTemplateForm(request.POST, tutor=request.user)
        if form.is_valid():
            template = form.save(commit=False)
            template.tutor = request.user
            template.save()
            return redirect('recurring_templates_list')
    else:
        form = RecurringLessonTemplateForm(tutor=request.user)
    return render(request, 'scheduler/tutor/recurring_templates/form.html', {'form': form, 'create': True})

@login_required
@user_passes_test(is_tutor)
def recurring_template_edit(request, template_id):
    template = get_object_or_404(RecurringLessonTemplate, id=template_id, tutor=request.user)
    if request.method == 'POST':
        form = RecurringLessonTemplateForm(request.POST, instance=template, tutor=request.user)
        if form.is_valid():
            form.save()
            return redirect('recurring_templates_list')
    else:
        form = RecurringLessonTemplateForm(instance=template, tutor=request.user)
    return render(request, 'scheduler/tutor/recurring_templates/form.html', {'form': form, 'create': False})

@login_required
@user_passes_test(is_tutor)
def manage_students(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        student_id = request.POST.get('student_id')
        
        if action == 'add':
            email = request.POST.get('email')
            try:
                student = User.objects.get(email=email, groups__name='Students')
                # Проверяем, не добавлен ли уже этот студент
                if not TutorStudent.objects.filter(tutor=request.user, student=student).exists():
                    TutorStudent.objects.create(
                        tutor=request.user,
                        student=student,
                        subjects=request.POST.getlist('subjects')
                    )
                    messages.success(request, f'Ученик {student.get_full_name()} успешно добавлен')
                else:
                    messages.error(request, 'Этот ученик уже добавлен к вам')
            except User.DoesNotExist:
                messages.error(request, 'Ученик с таким email не найден')
        
        elif action == 'remove' and student_id:
            try:
                relation = TutorStudent.objects.get(tutor=request.user, student_id=student_id)
                relation.is_active = False
                relation.save()
                messages.success(request, 'Ученик успешно удален из вашего списка')
            except TutorStudent.DoesNotExist:
                messages.error(request, 'Ученик не найден')
        
        elif action == 'update' and student_id:
            try:
                relation = TutorStudent.objects.get(tutor=request.user, student_id=student_id)
                relation.subjects = request.POST.getlist('subjects')
                relation.save()
                messages.success(request, 'Информация об ученике обновлена')
            except TutorStudent.DoesNotExist:
                messages.error(request, 'Ученик не найден')
    
    # Получаем всех активных учеников
    students = TutorStudent.objects.filter(
        tutor=request.user,
        is_active=True
    ).select_related('student')
    
    return render(request, 'scheduler/tutor/manage_students.html', {
        'students': students,
        'subjects': dict(Lesson.SUBJECT_CHOICES)
    })

@login_required
def manage_lesson_photos(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    # Проверяем, что пользователь имеет доступ к уроку
    if not (request.user == lesson.student or request.user == lesson.time_slot.tutor):
        messages.error(request, 'У вас нет доступа к этому уроку')
        return redirect('student_dashboard' if is_student(request.user) else 'tutor_dashboard')
    
    if request.method == 'POST':
        form = LessonPhotosForm(request.POST, request.FILES)
        if form.is_valid():
            photos = request.FILES.getlist('photos')
            for photo in photos:
                LessonPhoto.objects.create(lesson=lesson, photo=photo)
            messages.success(request, 'Фотографии успешно добавлены')
            return redirect('manage_lesson_photos', lesson_id=lesson.id)
    else:
        form = LessonPhotosForm()
    
    photos = lesson.photos.all().order_by('-created_at')
    return render(request, 'scheduler/lesson/photos.html', {
        'lesson': lesson,
        'photos': photos,
        'form': form
    })

@login_required
def delete_lesson_photo(request, photo_id):
    photo = get_object_or_404(LessonPhoto, id=photo_id)
    lesson = photo.lesson
    
    # Проверяем, что пользователь имеет доступ к уроку
    if not (request.user == lesson.student or request.user == lesson.time_slot.tutor):
        messages.error(request, 'У вас нет доступа к этой фотографии')
        return redirect('student_dashboard' if is_student(request.user) else 'tutor_dashboard')
    
    if request.method == 'POST':
        # Удаляем файлы
        if photo.photo:
            if os.path.exists(photo.photo.path):
                os.remove(photo.photo.path)
        if photo.thumbnail:
            if os.path.exists(photo.thumbnail.path):
                os.remove(photo.thumbnail.path)
        
        photo.delete()
        messages.success(request, 'Фотография удалена')
        return redirect('manage_lesson_photos', lesson_id=lesson.id)
    
    return render(request, 'scheduler/lesson/delete_photo.html', {
        'photo': photo,
        'lesson': lesson
    })
