# Generated by Django 4.0.5 on 2022-08-18 15:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='Squadron-Organized Event', max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='EmptyLesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
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
            name='PerformanceObjective',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('po', models.CharField(max_length=3, unique=True)),
                ('po_title', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Senior',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
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
                ('lesson_id', models.PositiveIntegerField()),
                ('object_id', models.PositiveIntegerField(null=True)),
                ('location', models.CharField(max_length=128)),
                ('finished', models.BooleanField(default=False)),
                ('plan', models.CharField(blank=True, default='', max_length=1000)),
                ('content_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.contenttype')),
                ('level', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='training.level')),
            ],
            options={
                'ordering': ['lesson_id'],
            },
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
                ('senior', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training.senior')),
                ('teach', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training.teach')),
            ],
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('eocode', models.CharField(max_length=64, unique=True)),
                ('title', models.CharField(max_length=256)),
                ('po', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='training.performanceobjective')),
            ],
        ),
        migrations.AddIndex(
            model_name='teach',
            index=models.Index(fields=['content_type', 'object_id'], name='training_te_content_626850_idx'),
        ),
    ]
