from django.db import models
from training.models import Teach
from django.conf import settings

from django.template.loader import render_to_string
from django.core.mail import send_mail

# Create your models here.
class Email(models.Model):
    sent_from = models.EmailField()
    sent_to = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()

    @classmethod
    def create(cls, sent_form: str, sent_to: str, subject: str, message: str):
        return cls.objects.create(
            sent_form=sent_form, sent_to=sent_to, subject=subject, message=message
        )

    def send_training_email(subject, message, sent_to):
        return send_mail(
            subject, message, settings.EMAIL_HOST_USER, [sent_to], fail_silently=False
        )

    @classmethod
    def send_assignment_email(cls, user, teach: Teach, role: str):
        template = "emails/assignment_email.html"
        subject = "Banshee Teach Assignment Notification"
        context = {"user": user, "teach": teach, "role": role}

        message = render_to_string(template, context)
        return cls.send_training_email(subject, message, [user.email])
