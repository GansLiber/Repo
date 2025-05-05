from django.db import models

from django.contrib.auth import get_user_model

class TimeSlot(models.Model):
    datetime = models.DateTimeField()
    student = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.datetime} - {'Booked' if self.student else 'Available'}"
