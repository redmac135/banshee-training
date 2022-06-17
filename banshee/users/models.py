from django.db import models

# Create your models here.
class TrainingSetting(models.Model):
    duedateoffset = models.IntegerField() # days before lesson

    def __str__(self):
        return self.pk

    @classmethod
    def create(cls, *args, **kwargs):
        if cls.objects.all().exists():
            cls.objects.all().delete()
        settings = cls(*args, **kwargs)
        settings.save()
        return settings