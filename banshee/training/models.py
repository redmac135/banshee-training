from datetime import datetime
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

# Managing People

# Important: users.forms requires senior numbers be unique
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
        return cls.objects.filter(number__lte=4, number__gte=1)

    @classmethod
    def get_seniors(cls):
        return cls.objects.filter(number__gte=5)

    @classmethod
    def get_senior_level_choices(cls):
        seniors = cls.get_seniors()
        return [(level.number, level.name) for level in seniors]

    @classmethod
    def senior_numbertoinstance(cls, number):
        return cls.objects.get(number=number)

    def get_next(self):
        found = False
        levels = self.objects.all()
        for level in levels:
            if found:
                return level
            if self == level:
                found = True
        return None

    def get_prev(self):
        found = False
        levels = self.objects.all().reverse()
        for level in levels:
            if found:
                return level
            if self == level:
                found = True
        return None


class Senior(models.Model):
    RANK_CHOICES = [
        (1, "Cdt"),
        (2, "Lac"),
        (3, "Cpl"),
        (4, "FCpl"),
        (5, "Sgt"),
        (6, "FSgt"),
        (7, "WO2"),
        (8, "WO1"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    rank = models.IntegerField()
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return (
            self.rank_to_str(self.rank)
            + ". "
            + self.user.last_name
            + ", "
            + self.user.first_name
        )

    class Meta:
        ordering = ["level", "rank"]

    @classmethod
    def by_level(cls, level):
        return cls.objects.filter(level=level)

    @classmethod
    def rank_to_str(cls, number):
        ranks = dict(cls.RANK_CHOICES)
        return ranks[number]


# Managing Lessons
class Teach(models.Model):
    lesson_id = (
        models.PositiveIntegerField()
    )  # For joining 2 period lessons or mulilevel lessons

    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content = GenericForeignKey("content_type", "object_id")

    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True)
    location = models.CharField(max_length=128)
    finished = models.BooleanField(default=False)
    plan = models.CharField(
        max_length=1000, default="", blank=True
    )  # Link to lesson plan

    def __str__(self):
        return str(self.content)

    class Meta:
        ordering = ["lesson_id"]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    @classmethod
    def get_next_lesson_id(cls):
        queryset = (
            cls.objects.all()
        )  # don't use class get_objects to prevent duplicate ids
        if not queryset:
            return 1

        largest_id = queryset[0].lesson_id
        return largest_id + 1

    @classmethod
    def create(cls, level: Level, content=None, id: int = None):
        if id == None:
            id = cls.get_next_lesson_id()

        if content == None:
            content = EmptyLesson.create()

        instance = cls.objects.create(lesson_id=id, content=content, level=level)
        return instance

    def format_html_block(self):
        content_class = type(self.content).__name__

        if content_class == "Lesson":
            return Lesson.format_html_block(self.content, self)
        if content_class == "EmptyLesson":
            return EmptyLesson.format_html_block()
        return "UNKNOWN CONTENT CLASS NAME"


class PerformanceObjective(models.Model):
    po = models.CharField(max_length=3, unique=True)
    po_title = models.CharField(max_length=256)

    def __str__(self):
        return self.po

    @classmethod
    def create(cls, po: str, po_title: str):
        if cls.objects.filter(po=po).exists():
            return cls.objects.get(po=po)

        instance = cls.objects.create(po=po, po_title=po_title)
        return instance


class Lesson(models.Model):
    po = models.ForeignKey(PerformanceObjective, on_delete=models.SET_NULL, null=True)
    eocode = models.CharField(
        max_length=64, unique=True
    )  # Should be in the format 'M336.04'
    title = models.CharField(max_length=256)
    teach = GenericRelation(Teach)

    def __str__(self):
        return self.eocode

    @classmethod
    def create(cls, eocode: str, po_title: str, title: str, po: str = None):
        if cls.objects.filter(eocode=eocode).exists():
            return cls.objects.get(eocode=eocode)

        if po == None:
            po = eocode[1:4]

        po_instance = PerformanceObjective.create(po, po_title)
        instance = cls.objects.create(po=po_instance, eocode=eocode, title=title)
        return instance

    # This method is for the utils.trainingdayschedule class
    def format_html_block(self, teach: Teach):
        block = f"<p class='mb-2 font-bold tracking-tight text-clr-5'>{self.eocode}</p>"

        instructors = ""
        for instructor in MapSeniorTeach.get_instructors(teach):
            instructors += f"{instructor}<br>"
        block += f"<p class='font-normal text-gray-400'>{instructors}</p>"

        return block


class Activity(models.Model):
    title = models.CharField(max_length=256, default="Squadron-Organized Event")
    teach = GenericRelation(Teach)

    def __str__(self):
        return self.title


# Blank object for empty teach instances
class EmptyLesson(models.Model):
    teach = GenericRelation(Teach)

    def __str__(self):
        return "Empty Lesson Placeholder"

    @classmethod
    def create(cls):
        return cls.objects.create()

    @classmethod
    def format_html_block(self):
        return "<div class='pb-2 font-bold text-lg tracking-tight text-gray-400 text-center h-full place-items-center grid'>UNASSIGNED</div>"


class MapSeniorTeach(models.Model):
    IC_ROLE_NAME = "ic"

    teach = models.ForeignKey(Teach, on_delete=models.CASCADE)
    senior = models.ForeignKey(Senior, on_delete=models.CASCADE)
    role = models.CharField(max_length=32)

    @classmethod
    def get_ic(cls, teach: Teach):
        if cls.objects.filter(teach=teach, role=cls.IC_ROLE_NAME).exists():
            return cls.objects.get(teach=teach, role=cls.IC_ROLE_NAME)
        else:
            return False

    @classmethod
    def get_instructors(cls, teach: Teach):
        queryset = cls.objects.filter(teach=teach)

        instructors = []
        for object in queryset:
            instructors.append((object.role, object.senior))

        return instructors


class TrainingPeriod(models.Model):
    lessons = models.ManyToManyField(Teach)

    # create a training period with a teach instance for each level
    @classmethod
    def create_fulllesson(cls):
        instance = cls.objects.create()
        levels = Level.get_juniors()
        for level in levels:
            teach = Teach.create(level)
            instance.lessons.add(teach)
        return instance

    @classmethod
    def create_fullact(cls):
        instance = cls.objects.create()
        levels = Level.get_juniors()
        teach_id = Teach.get_next_lesson_id()
        for level in levels:
            teach = Teach.create(level, id=teach_id)
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
    def create(cls, date: datetime, p1o: int = 0, p2o: int = 0, p3o: int = 0):
        instance = cls()
        instance.date = date
        instance.p1 = cls.PERIOD_OBJECTS[p1o]()
        instance.p2 = cls.PERIOD_OBJECTS[p2o]()
        instance.p3 = cls.PERIOD_OBJECTS[p3o]()

        masterinstance = Teach.create(Level.get_master())
        instance.masterteach = masterinstance

        instance.save()

        return instance

    @classmethod
    def get_nights(cls, **kwargs):
        return cls.objects.filter(**kwargs)
