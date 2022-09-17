from django.db import models
from django.urls import reverse

# Account Activation Imports
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from emails.models import Email

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

    @classmethod
    def get_duedateoffset(cls):
        instance = cls.create()
        return instance.duedateoffset


class AuthorizedEmail(models.Model):
    email = models.EmailField(unique=True)
    is_officer = models.BooleanField(default=False)

    def __str__(self):
        return self.email

    def get_absolute_url(self):
        return reverse("authemail-detail", args=[self.pk])

    def status_to_str(self):
        if self.is_officer == False:
            return "Cadet"
        else:
            return "Officer"

    @classmethod
    def authorize_email(cls, email: str, is_officer: bool = False):
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
        email_list = []
        for obj in cls.objects.all():
            email_list.append(
                {
                    "email": obj.email,
                    "status": obj.status_to_str(),
                    "detail_url": obj.get_absolute_url(),
                }
            )
        return email_list


class AccountActivation:
    def send_activation_email(user, request):
        current_site = get_current_site(request)
        subject = "Welcome to the Banshee Training App! Activate your Account"
        message = render_to_string(
            "emails/account_activation_email.html",
            {
                "user": user,
                "domain": current_site.domain,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": account_activation_token.make_token(user),
            },
        )
        Email.send_training_email(subject, message, user.email)
