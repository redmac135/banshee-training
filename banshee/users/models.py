from django.db import models
from django.urls import reverse

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

class AuthorizedEmail(models.Model):
    email = models.EmailField(unique=True)
    is_officer = models.BooleanField(default=False)

    def __str__(self):
        return self.email
    
    def get_absolute_url(self):
        return reverse('authemail-detail', pk=self.pk)

    @classmethod
    def authorize_email(cls, email: str, is_officer: bool=False):
        return cls.objects.create(email=email, is_officer=is_officer)
    
    @classmethod
    def unauthorize_pk(cls, pk):
        instance = cls.objects.get(id=pk)
        return instance.delete()

    @classmethod
    def cadet_email_exists(cls, email: str):
        return cls.objects.filter(email=email, is_officer=False).exists()

    @classmethod
    def officer_email_exists(cls, email: str):
        return cls.objects.filter(email=email, is_officer=True).exists()
    
    @classmethod
    def get_list_of_emails(cls):
        return cls.objects.all().values_list('email', 'is_officer')