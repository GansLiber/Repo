from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import TimeSlot, Lesson, RecurringLessonTemplate

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя пользователя'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'})
    )

class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['datetime', 'duration', 'notes']
        widgets = {
            'datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'duration': forms.NumberInput(attrs={'min': '30', 'max': '180', 'step': '30'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class BookSlotForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['subject', 'notes']
        widgets = {
            'subject': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'notes': forms.Textarea(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'rows': 3}),
        }

    photos = MultipleFileField(
        widget=MultipleFileInput(attrs={'class': 'hidden'}),
        required=False
    )

class RecurringLessonTemplateForm(forms.ModelForm):
    class Meta:
        model = RecurringLessonTemplate
        fields = ['student', 'weekday', 'time', 'duration', 'subject', 'start_date', 'end_date', 'is_active']
        widgets = {
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        } 