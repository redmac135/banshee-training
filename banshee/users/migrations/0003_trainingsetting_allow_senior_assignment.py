# Generated by Django 4.0.5 on 2022-09-23 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_authorizedemail"),
    ]

    operations = [
        migrations.AddField(
            model_name="trainingsetting",
            name="allow_senior_assignment",
            field=models.BooleanField(default=False),
        ),
    ]
