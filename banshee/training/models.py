from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

# Managing People
class Level(models.Model):
    MASTER_LEVEL_NAME = "ms"  # must be 2 characters

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
            return cls.objects.create(name=cls.MASTER_LEVEL_NAME, number=0)

    @classmethod
    def get_juniors(cls):
        return cls.objects.filter(number__lte=4)

    @classmethod
    def get_seniors(cls):
        return cls.objects.filter(number__gte=5)


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
        ordering = ["level", "rank"]

    @classmethod
    def by_level(cls, level):
        return cls.objects.filter(level=level)

    @classmethod
    def get_available_seniors(cls):
        return [
            (str(senior.id), str(senior)) for senior in cls.objects.filter(user=None)
        ]


# Managing Lessons
class Teach(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey('content_type', 'object_id')

    levels = models.ManyToManyField(Level)
    finished = models.BooleanField(default=False)
    plan = models.CharField(
        max_length=1000, default="", blank=True
    )  # Link to lesson plan

    def __str__(self):
        return str(self.content)

    class Meta:
        indexes = [models.Index(fields=["content_type", "object_id"])]


class Lesson(models.Model):
    po = models.IntegerField()
    eocode = models.CharField(max_length=64)
    title = models.CharField(max_length=256)
    teach = GenericRelation(Teach)

    def __str__(self):
        return self.eocode


class Activity(models.Model):
    title = models.CharField(max_length=256, default="Squadron-Organized Event")

    def __str__(self):
        return self.title


class MapSeniorTeach(models.Model):
    IC_ROLE_NAME = "ic"

    teach = models.ForeignKey(Teach, on_delete=models.CASCADE)
    senior = models.ForeignKey(Senior, on_delete=models.CASCADE)
    role = models.CharField(max_length=32)

    @classmethod
    def get_ic(cls, lesson):
        if cls.objects.filter(lesson=lesson, role=cls.IC_ROLE_NAME).exists():
            return cls.objects.get(lesson=lesson, role=cls.IC_ROLE_NAME)
        else:
            return False


class TrainingPeriod(models.Model):
    lessons = models.ManyToManyField(Teach)

    # create a training period with a teach instance for each level
    @classmethod
    def create_fulllesson(cls):
        instance = cls.objects.create()
        levels = Level.get_juniors()
        for level in levels:
            teach = Teach.objects.create(content=None)
            teach.levels.add(level)
            instance.lessons.add(teach)
        return instance

    @classmethod
    def create_fullact(cls):
        instance = cls.objects.create()
        levels = Level.get_juniors()
        teach = Teach.objects.create(content=None)
        for level in levels:
            teach.levels.add(level)
        instance.lessons.add(teach)
        return instance

    @classmethod
    def create_blank(cls):
        instance = cls.objects.create()
        return instance


class TrainingNight(models.Model):
    date = models.DateField()
    p1 = models.OneToOneField(
        TrainingPeriod, related_name="periodone", on_delete=models.SET_NULL, null=True
    )
    p2 = models.OneToOneField(
        TrainingPeriod, related_name="periodtwo", on_delete=models.SET_NULL, null=True
    )
    p3 = models.OneToOneField(
        TrainingPeriod, related_name="periodthree", on_delete=models.SET_NULL, null=True
    )
    masterteach = models.ForeignKey(Teach, on_delete=models.SET_NULL, null=True)
    excused = models.ManyToManyField(Senior)

    def __str__(self):
        return str(self.date)

    class Meta:
        ordering = ["-date"]

    PERIOD_OBJECTS = {
        0: TrainingPeriod.create_fulllesson,
        1: TrainingPeriod.create_fullact,
        2: TrainingPeriod.create_blank,
    }

    @classmethod
    def create(cls, date, p1o, p2o, p3o):
        instance = cls()
        instance.date = date
        instance.p1 = cls.PERIOD_OBJECTS[p1o]
        instance.p2 = cls.PERIOD_OBJECTS[p2o]
        instance.p3 = cls.PERIOD_OBJECTS[p3o]

        masterinstance = Teach.objects.create(content=None)
        masterinstance.levels.add(Level.get_master())
        instance.masterteach = masterinstance

        instance.save()

        return instance

    @classmethod
    def get_list(cls, **kwargs):
        return cls.objects.filter(**kwargs)
