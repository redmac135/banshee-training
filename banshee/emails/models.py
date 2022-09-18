from django.db import models
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
    def create(
        cls,
        sent_to: str,
        subject: str,
        message: str,
        sent_from=settings.EMAIL_HOST_USER,
    ):
        return cls.objects.create(
            sent_to=sent_to,
            subject=subject,
            sent_from=sent_from,
            message=message,
        )

    @classmethod
    def send_training_email(cls, subject, message, sent_to):
        cls.create(sent_to=sent_to, subject=subject, message=message)
        return send_mail(
            subject, message, settings.EMAIL_HOST_USER, [sent_to], fail_silently=False
        )

    @classmethod
    def send_teach_assignment_email(cls, user, teach, role: str):
        template = "emails/teach_assignment_email.html"
        subject = "Banshee Teach Assignment Notification"
        context = {"user": user, "teach": teach, "role": role}

        message = render_to_string(template, context)
        return cls.send_training_email(subject, message, user.email)

    @classmethod
    def send_night_assignment_email(cls, user, night, role: str):
        template = "emails/night_assignment_email.html"
        subject = "Banshee Night Assignment Notification"
        context = {"user": user, "night": night, "role": role}

        message = render_to_string(template, context)
        return cls.send_training_email(subject, message, user.email)
