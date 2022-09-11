from django.db import models

# Create your models here.
class TrainingSetting(models.Model):
    duedateoffset = models.IntegerField(default=7)  # days before lesson

    def save(self, *args, **kwargs):
        self.pk = 1
        super(TrainingSetting, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def create(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
