# Generated by Django 4.0.5 on 2022-11-24 01:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_delete_authorizedemail"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuthorizedUsername",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("username", models.CharField(max_length=32)),
            ],
        ),
    ]
