from django.db import models

# Create your models here.
class TrainingSetting(models.Model):
    duedateoffset = models.IntegerField(default=7)  # days before lesson
    allow_senior_assignment = models.BooleanField(
        default=False
    )  # Should assign senior allow permission level 2

    def save(self, *args, **kwargs):
        self.pk = 1
        super(TrainingSetting, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def create(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def get_duedateoffset(cls):
        instance = cls.create()
        return instance.duedateoffset

    @classmethod
    def get_senior_assignment(cls):
        instance = cls.create()
        return instance.allow_senior_assignment
