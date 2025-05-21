from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import TutorSchedule, TimeSlot, Lesson, LessonPhoto, RecurringLessonTemplate, UserProfile, ResourceLink, TutorStudent

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

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

@admin.register(ResourceLink)
class ResourceLinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_by', 'created_at')
    list_filter = ('category', 'created_by')
    search_fields = ('title', 'description')
    filter_horizontal = ('shared_with',)

@admin.register(TutorStudent)
class TutorStudentAdmin(admin.ModelAdmin):
    list_display = ('tutor', 'student', 'is_active', 'created_at')
    list_filter = ('is_active', 'tutor', 'created_at')
    search_fields = ('tutor__username', 'tutor__first_name', 'student__username', 'student__first_name')
    raw_id_fields = ('tutor', 'student')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "student":
            kwargs["queryset"] = User.objects.filter(groups__name='Students')
        elif db_field.name == "tutor":
            kwargs["queryset"] = User.objects.filter(groups__name='Tutors')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)