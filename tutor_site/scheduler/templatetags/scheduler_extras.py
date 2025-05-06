from django import template
from django.utils.dateformat import format
from datetime import datetime

register = template.Library()

@register.filter
def date_with_weekday(value):
    if not value:
        return ""
    weekdays = {
        0: 'понедельник',
        1: 'вторник',
        2: 'среда',
        3: 'четверг',
        4: 'пятница',
        5: 'суббота',
        6: 'воскресенье'
    }
    weekday = weekdays[value.weekday()]
    return f"{value.strftime('%d.%m.%Y %H:%M')} ({weekday})" 