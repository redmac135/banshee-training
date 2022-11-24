from django.db import models
from django.urls import reverse

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


class AuthorizedUsername(models.Model):
    username = models.CharField(max_length=32, unique=True)

    def get_absolute_url(self):
        return reverse("authusername-detail", args=[self.pk])

    @classmethod
    def username_allowed(cls, username: str):
        return True if cls.objects.filter(username=username).exists() else False

    @classmethod
    def authorize_username(cls, username: str):
        return cls.objects.get_or_create(username=username)

    @classmethod
    def unauthorize_pk(cls, pk):
        cls.objects.filter(pk=pk).delete()
        return True

    @classmethod
    def all_usernames(cls):
        return cls.objects.all()
