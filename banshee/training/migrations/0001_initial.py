# Generated by Django 4.0.5 on 2022-08-04 19:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('po', models.IntegerField()),
                ('eocode', models.CharField(max_length=7)),
                ('title', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Level',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=2)),
                ('number', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Senior',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('firstname', models.CharField(max_length=100)),
                ('lastname', models.CharField(max_length=100)),
                ('rank', models.IntegerField()),
                ('level', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='training.level')),
                ('user', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['level', 'rank'],
            },
        ),
        migrations.CreateModel(
            name='Teach',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lesson', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='training.lesson')),
                ('level', models.ManyToManyField(to='training.level')),
            ],
        ),
        migrations.CreateModel(
            name='TrainingPeriod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lessons', models.ManyToManyField(to='training.teach')),
            ],
        ),
        migrations.CreateModel(
            name='TrainingNight',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('excused', models.ManyToManyField(to='training.senior')),
                ('masterteach', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='training.teach')),
                ('p1', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='periodone', to='training.trainingperiod')),
                ('p2', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='periodtwo', to='training.trainingperiod')),
                ('p3', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='periodthree', to='training.trainingperiod')),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='MapSeniorTeach',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(max_length=32)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training.lesson')),
                ('senior', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training.senior')),
            ],
        ),
    ]
