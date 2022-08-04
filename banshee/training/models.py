from django.db import models
from django.contrib.auth.models import User

# Managing People
class Level(models.Model):
    MASTER_LEVEL_NAME = 'ms' # must be 2 characters

    name = models.CharField(max_length=2)
    number = models.IntegerField()

    def __str__(self):
        return self.name
    
    # The level for the teach instance attached to every training night for NCOs and OnCalls
    @classmethod
    def get_master(cls):
        if cls.objects.filter(number=0).exists():
            return cls.objects.get(number=0)
        else:
            return cls.objects.create(
                name = cls.MASTER_LEVEL_NAME,
                number = 0
            )

class Senior(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    rank = models.IntegerField()
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.rank + ". " + self.user.last_name + ", " + self.user.first_name

    class Meta:
        ordering = ['level', 'rank']

    @classmethod
    def by_level(cls, level):
        return cls.objects.filter(level=level)
    
    @classmethod
    def get_available_seniors(cls):
        return [(str(senior.id), str(senior)) for senior in cls.objects.filter(user = None)]

# Managing Lessons
class Lesson(models.Model):
    po = models.IntegerField()
    eocode = models.CharField(max_length=7)
    title = models.CharField(max_length=256)

    def __str__(self):
        return self.eocode

class MapSeniorTeach(models.Model):
    IC_ROLE_NAME = 'ic'

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    senior = models.ForeignKey(Senior, on_delete=models.CASCADE)
    role = models.CharField(max_length=32)

    @classmethod
    def get_ic(cls, lesson):
        if cls.objects.filter(lesson=lesson, role=cls.IC_ROLE_NAME).exists():
            return cls.objects.get(lesson=lesson, role=cls.IC_ROLE_NAME)
        else:
            return False

class Teach(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True)
    levels = models.ManyToManyField(Level)
    finished = models.BooleanField(default=False)
    plan = models.CharField(max_length=1000, default='', blank=True) # Link to lesson plan

    def __str__(self):
        if MapSeniorTeach.get_ic(self.lesson):
            return MapSeniorTeach.get_ic(self.lesson).senior + " " + self.lesson
        else:
            return "No IC " + self.lesson

class TrainingPeriod(models.Model):
    lessons = models.ManyToManyField(Teach)

    # create a training period with a teach instance for each level
    @classmethod
    def create_full(cls):
        instance = cls.objects.create()
        levels = Level.objects.all()
        for level in levels:
            teach = Teach.objects.create(
                lesson = None
            )
            teach.levels.add(level)
            instance.lessons.add(teach)
        return instance

class TrainingNight(models.Model):
    date = models.DateField()
    p1 = models.OneToOneField(TrainingPeriod, related_name='periodone', on_delete=models.SET_NULL, null=True)
    p2 = models.OneToOneField(TrainingPeriod, related_name='periodtwo', on_delete=models.SET_NULL, null=True)
    p3 = models.OneToOneField(TrainingPeriod, related_name='periodthree', on_delete=models.SET_NULL, null=True)
    masterteach = models.ForeignKey(Teach, on_delete=models.SET_NULL, null=True)
    excused = models.ManyToManyField(Senior)

    def __str__(self):
        return str(self.date)

    class Meta:
        ordering = ['-date']

    @classmethod
    def create(cls, date):
        instance = cls()
        instance.date = date
        instance.p1 = TrainingPeriod.create_full()
        instance.p2 = TrainingPeriod.create_full()
        instance.p3 = TrainingPeriod.create_full()

        masterinstance = Teach.objects.create(lesson = None)
        masterinstance.levels.add(Level.get_master())
        instance.masterteach = masterinstance

        instance.save()

        return instance

    @classmethod
    def get_list(cls, **kwargs):
        return cls.objects.filter(**kwargs)