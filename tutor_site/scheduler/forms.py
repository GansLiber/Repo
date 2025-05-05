from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import TimeSlot

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