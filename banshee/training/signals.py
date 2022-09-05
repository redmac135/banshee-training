from django.dispatch import receiver
from .models import TrainingPeriod
from django.db.models.signals import pre_delete

@receiver(pre_delete, sender=TrainingPeriod)
def delete_trainingperiod(sender, instance: TrainingPeriod, **kwargs):
    for lesson in instance.lessons.all():
        lesson.delete()