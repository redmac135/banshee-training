# Generated by Django 4.0.5 on 2022-09-16 23:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("training", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="senior",
            name="permission_level",
            field=models.IntegerField(
                choices=[
                    (1, "Standard Instructor"),
                    (2, "Training Manager"),
                    (3, "Officer"),
                    (4, "Admin"),
                ],
                default=1,
            ),
        ),
    ]
