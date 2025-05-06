from django import template
from django.utils.dateformat import format
from datetime import datetime
from django.utils import timezone

register = template.Library()

@register.filter
def date_with_weekday(value):
    if not value:
        return ""
    weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    return f"{value.strftime('%d.%m.%Y')} ({weekdays[value.weekday()]})"

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key) 