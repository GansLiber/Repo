from django.db import migrations

def remove_duplicate_slots(apps, schema_editor):
    TimeSlot = apps.get_model('scheduler', 'TimeSlot')
    
    # Получаем все слоты, сгруппированные по преподавателю и времени
    slots = TimeSlot.objects.all().order_by('tutor_id', 'datetime')
    
    # Храним последний обработанный слот
    last_slot = None
    
    for slot in slots:
        if last_slot and slot.tutor_id == last_slot.tutor_id and slot.datetime == last_slot.datetime:
            # Если слот забронирован, оставляем его, иначе удаляем
            if slot.status == 'booked':
                last_slot.delete()
                last_slot = slot
            else:
                slot.delete()
        else:
            last_slot = slot

def reverse_remove_duplicates(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('scheduler', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_slots, reverse_remove_duplicates),
        migrations.AlterUniqueTogether(
            name='timeslot',
            unique_together={('tutor', 'datetime')},
        ),
    ] 