from django.contrib.auth.models import User
from training.models import Senior
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def update_user_senior(sender, instance, created, **kwargs):
    if created:
        Senior.objects.create(user=instance)
        instance.senior.save()


@receiver(post_save, sender=User)
def save_user_senior(sender, instance, **kwargs):
    instance.senior.save()
