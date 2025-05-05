from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from .models import TutorSchedule, TimeSlot, Lesson

def create_groups_and_permissions(**kwargs):
    # Create groups
    tutor_group, _ = Group.objects.get_or_create(name='Tutors')
    student_group, _ = Group.objects.get_or_create(name='Students')

    # Get content types
    tutor_schedule_ct = ContentType.objects.get_for_model(TutorSchedule)
    time_slot_ct = ContentType.objects.get_for_model(TimeSlot)
    lesson_ct = ContentType.objects.get_for_model(Lesson)

    # Tutor permissions
    tutor_permissions = Permission.objects.filter(
        Q(content_type=tutor_schedule_ct) |
        Q(content_type=time_slot_ct) |
        Q(content_type=lesson_ct)
    )
    tutor_group.permissions.set(tutor_permissions)

    # Student permissions
    student_permissions = Permission.objects.filter(
        Q(content_type=time_slot_ct, codename__in=['view_timeslot', 'change_timeslot']) |
        Q(content_type=lesson_ct, codename__in=['view_lesson', 'change_lesson'])
    )
    student_group.permissions.set(student_permissions) 