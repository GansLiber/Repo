from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import TutorSchedule, TimeSlot, Lesson, LessonPhoto, RecurringLessonTemplate

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'get_groups')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])
    get_groups.short_description = 'Группы'

@admin.register(TutorSchedule)
class TutorScheduleAdmin(admin.ModelAdmin):
    list_display = ('tutor', 'get_day_of_week_display', 'start_time', 'end_time', 'is_available')
    list_filter = ('tutor', 'day_of_week', 'is_available')
    search_fields = ('tutor__username', 'tutor__first_name', 'tutor__last_name')
    ordering = ('tutor', 'day_of_week', 'start_time')

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('datetime', 'tutor', 'student', 'status', 'duration')
    list_filter = ('status', 'tutor', 'datetime')
    search_fields = ('tutor__username', 'student__username', 'notes')
    date_hierarchy = 'datetime'
    ordering = ('-datetime',)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('time_slot', 'student', 'status', 'created_at')
    list_filter = ('status', 'student', 'time_slot__datetime')
    search_fields = ('student__username', 'homework', 'notes')
    date_hierarchy = 'time_slot__datetime'
    ordering = ('-time_slot__datetime',)

@admin.register(LessonPhoto)
class LessonPhotoAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'photo', 'thumbnail', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('lesson__student__username',)
    ordering = ('-created_at',)

@admin.register(RecurringLessonTemplate)
class RecurringLessonTemplateAdmin(admin.ModelAdmin):
    list_display = ('tutor', 'student', 'weekday', 'time', 'duration', 'subject', 'start_date', 'end_date', 'is_active')
    list_filter = ('tutor', 'student', 'weekday', 'is_active')
    search_fields = ('tutor__username', 'student__username', 'subject')
    ordering = ('-start_date',)

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)