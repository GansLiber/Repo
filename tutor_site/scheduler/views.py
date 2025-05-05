from django.shortcuts import render

from .models import TimeSlot

def schedule_view(request):
    slots = TimeSlot.objects.all().order_by('datetime')
    return render(request, 'scheduler/schedule.html', {'slots': slots})
