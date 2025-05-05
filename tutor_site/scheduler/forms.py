from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import TimeSlot, Lesson

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
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-md', 'rows': 3}),
        }

    photos = MultipleFileField(
        widget=MultipleFileInput(attrs={'class': 'hidden'}),
        required=False
    ) 