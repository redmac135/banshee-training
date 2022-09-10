# Generated by Django 4.0.5 on 2022-09-10 03:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("training", "0003_alter_teach_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="senior",
            name="permission_level",
            field=models.IntegerField(
                choices=[(1, "Standard Instructor"), (2, "Training Manager")], default=1
            ),
        ),
    ]
