from datetime import datetime, date, timedelta
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

from users.models import TrainingSetting

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

    STANDARD_INSTRUCTOR = 1
    TRAINING_MANAGER = 2
    PERMISSION_CHOICES = [
        (STANDARD_INSTRUCTOR, "Standard Instructor"),
        (TRAINING_MANAGER, "Training Manager"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    rank = models.IntegerField()
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True)
    permission_level = models.IntegerField(choices=PERMISSION_CHOICES, default=1)

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
    def get_all(cls):
        return cls.objects.all()

    @classmethod
    def get_by_id(cls, id: int):
        return cls.objects.get(id=id)

    @classmethod
    def rank_to_str(cls, number):
        ranks = dict(cls.RANK_CHOICES)
        return ranks[number]

    def is_training(self):
        if self.permission_level == 2:
            return True
        else:
            return False
class TrainingNight(models.Model):
    date = models.DateField(unique=True)
    excused = models.ManyToManyField(Senior)

    def __str__(self):
        return str(self.date)

    class Meta:
        ordering = ["-date"]

    @classmethod
    def create(cls, date: datetime, period_types: list = [0, 0, 0]):
        if cls.objects.filter(date=date).exists():
            return cls.objects.get(date=date)

        instance = cls()
        instance.date = date
        instance.save()

        for order, period_type in enumerate(period_types, 1):
            if period_type == 0:
                TrainingPeriod.create_fulllesson(instance, order)
            if period_type == 1:
                TrainingPeriod.create_fullact(instance, order)

        return instance

    @classmethod
    def get(cls, id):
        return cls.objects.get(pk=id)

    @classmethod
    def get_by_date(cls, date: datetime):
        return cls.objects.get(date=date)
    
    def get_absolute_url(self):
        return reverse("trainingnight", args=[self.id])

    @classmethod
    def get_nights(cls, **kwargs):
        return cls.objects.filter(**kwargs)

    def get_periods(self):
        return self.trainingperiod_set.all().order_by("order")


class TrainingPeriod(models.Model):
    night = models.ForeignKey(TrainingNight, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()

    def __str__(self):
        return str(self.order + 1)

    def get_teach_instances(self):
        queryset = Teach.get_by_period(self)
        return queryset

    # create a training period with a teach instance for each level
    @classmethod
    def create_fulllesson(cls, night, order):
        instance = cls.objects.create(night=night, order=order)
        levels = Level.get_juniors()
        for level in levels:
            Teach.create(level, instance)
        return instance

    @classmethod
    def create_fullact(cls, night, order):
        instance = cls.objects.create(night=night, order=order)
        levels = Level.get_juniors()
        teach_id = Teach.get_next_teach_id()
        for level in levels:
            Teach.create(level, instance, id=teach_id)
        return instance

# Managing Lessons
class Teach(models.Model):
    teach_id = (
        models.PositiveIntegerField()
    )  # For joining 2 period lessons or mulilevel lessons

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey("content_type", "object_id")

    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True)
    location = models.CharField(max_length=128)
    finished = models.BooleanField(default=False)
    plan = models.CharField(
        max_length=1000, default="", blank=True
    )  # Link to lesson plan

    period = models.ForeignKey(TrainingPeriod, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.content)

    class Meta:
        ordering = ["teach_id", "id"]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    @classmethod
    def get_next_teach_id(cls):
        largest = (
            cls.objects.all().last()
        )  # don't use class get_objects to prevent duplicate ids
        if not largest:
            return 1

        largest_id = largest.teach_id
        return largest_id + 1
    
    @classmethod
    def get_by_period(cls, period: TrainingPeriod):
        queryset = cls.objects.filter(period=period)
        return queryset.order_by("level__name")

    @classmethod
    def create(cls, level: Level, period: TrainingPeriod, content=None, id: int = None):
        if id == None:
            id = cls.get_next_teach_id()

        if content == None:
            content = EmptyLesson.create()

        instance = cls.objects.create(teach_id=id, period=period, content=content, level=level)
        return instance

    def get_absolute_url(self):
        return reverse("teach", args=[self.teach_id])

    def get_content_type(self):
        name = type(self.content).__name__
        return name

    def get_night_id(self):
        return self.period.night.id
    
    def get_date(self):
        return self.period.night.date

    def format_html_block(self):
        self = self.get_parent_instance()
        content_class = self.get_content_type()

        if content_class == "Lesson":
            return Lesson.format_html_block(self.content, self)
        if content_class == "Activity":
            return Activity.format_html_block(self.content, self)
        if content_class == "EmptyLesson":
            return EmptyLesson.format_html_block()
        return "UNKNOWN CONTENT CLASS NAME"

    @classmethod
    def get_by_teach_id(cls, teach_id):
        instances = cls.objects.filter(teach_id=teach_id)
        return instances.first()

    def get_parent_instance(self):
        return self.get_by_teach_id(self.teach_id)
    
    @classmethod
    def get_neighbour_instances(cls, teach_id):
        return cls.objects.filter(teach_id=teach_id)
    
    def get_level_list(self):
        queryset = self.get_neighbour_instances(self.teach_id)
        instances = queryset.values_list("level", flat=True)
        unique_instances = list(set(instances))
        return unique_instances
    
    def get_period_list(self):
        queryset = self.get_neighbour_instances(self.teach_id)
        instances = queryset.values_list("period__order", flat=True)
        unique_instances = list(set(instances))
        return unique_instances
    
    def get_status(self):
        if self.finished == True:
            return "Submitted"

        today = date.today()
        settings = TrainingSetting.create()
        offset = settings.duedateoffset
        teach_date = self.get_date()

        if teach_date < today + timedelta(days=offset):
            return "Not Submitted"
        else:
            return "Missing"


    def get_content_attributes(self):
        self = self.get_parent_instance()
        content_class = self.get_content_type()

        if content_class == "Lesson":
            return Lesson.get_content_attributes(self.content)
        if content_class == "Activity":
            return Activity.get_content_attributes(self.content)
        return {}

    def change_content(self, content):
        old_content = self.content

        self.content = content
        self.save()

        if type(old_content) == EmptyLesson:
            old_content.delete()


class PerformanceObjective(models.Model):
    po = models.CharField(max_length=3, unique=True)
    po_title = models.CharField(max_length=256, blank=True, null=True)

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
    def create(cls, eocode: str, title: str, po_title: str = None, po: str = None):
        if cls.objects.filter(eocode=eocode).exists():
            instance = cls.objects.get(eocode=eocode)
            if not instance.title == title:
                instance.change_title(title)
            return cls.objects.get(eocode=eocode)

        if po == None:
            po = eocode[1:4]

        po_instance = PerformanceObjective.create(po, po_title)
        instance = cls.objects.create(po=po_instance, eocode=eocode, title=title)
        return instance

    @classmethod
    def get_title(cls, eocode: str):
        if cls.objects.filter(eocode=eocode).exists():
            instance = cls.objects.get(eocode=eocode)
            return instance.title
        return False

    def change_title(self, title):
        self.title = title
        self.save()

    # This method is for the utils.trainingdayschedule class
    def format_html_block(self, teach: Teach):
        block = "<p class='tracking-tight text-gray-400 leading-none'>Lesson</p>"
        block += (
            f"<p class='mb-2 font-bold tracking-tight text-clr-5'>{self.eocode}</p>"
        )

        instructors = ""
        for role, instructor in MapSeniorTeach.get_instructors(teach):
            instructors += f"{role}: {instructor}<br>"
        block += f"<p class='font-normal text-gray-400'>{instructors}</p>"

        return block

    def get_content_attributes(self):
        return [("EO Code", self.eocode), ("Title", self.title)]


class Activity(models.Model):
    title = models.CharField(max_length=256, default="Squadron-Organized Event")
    teach = GenericRelation(Teach)

    def __str__(self):
        return self.title

    @classmethod
    def create(cls, title: str):
        instance = cls.objects.create(title=title)
        return instance

    # This method is for the utils.trainingdayschedule class
    def format_html_block(self, teach: Teach):
        block = "<p class='tracking-tight text-gray-400 leading-none'>Activity</p>"
        block += f"<p class='mb-2 font-bold tracking-tight text-clr-5'>{self.title}</p>"

        instructors = ""
        for instructor in MapSeniorTeach.get_instructors(teach):
            instructors += f"{instructor}<br>"
        block += f"<p class='font-normal text-gray-400'>{instructors}</p>"

        return block

    def get_content_attributes(self):
        return ["Title", self.title]


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
        return "<div class='text-center h-full font-bold text-lg tracking-tight text-gray-400'>UNASSIGNED</div>"


class MapSeniorTeach(models.Model):
    IC_ROLE_NAME = "ic"

    teach = models.ForeignKey(Teach, on_delete=models.CASCADE)
    senior = models.ForeignKey(Senior, on_delete=models.CASCADE)
    role = models.CharField(max_length=32)

    def __str__(self):
        return str(self.teach.teach_id) + " " + str(self.senior)

    @classmethod
    def get_ic(cls, teach: Teach):
        if cls.objects.filter(teach=teach, role=cls.IC_ROLE_NAME).exists():
            return cls.objects.get(teach=teach, role=cls.IC_ROLE_NAME)
        else:
            return False

    @classmethod
    def get_teach_queryset(cls, teach: Teach):
        queryset = cls.objects.filter(teach=teach)
        return queryset

    @classmethod
    def get_instructors(cls, teach: Teach):
        queryset = cls.get_teach_queryset(teach)

        instructors = []
        for object in queryset:
            instructors.append((object.role, object.senior))

        return instructors

    @classmethod
    def get_senior_queryset_after_date(cls, senior: Senior, date: date):
        queryset = cls.objects.filter(
            senior=senior,
            teach__period__night__date__gte=date,  # teach > trainingperiod > trainingnight date is before date
        )
        return queryset

class MapSeniorNight(models.Model):
    night = models.ForeignKey(TrainingNight, on_delete=models.CASCADE)
    senior = models.ForeignKey(Senior, on_delete=models.CASCADE)
    role = models.CharField(max_length=32)

    def __str__(self):
        return self.role + " for " + str(self.night.date) + " " + str(self.senior)
    
    @classmethod
    def get_night_queryset(cls, night: TrainingNight):
        queryset = cls.objects.filter(night=night)
        return queryset

    @classmethod
    def get_instructors(cls, night: TrainingNight):
        queryset = cls.get_night_queryset(night)

        instructors = []
        for object in queryset:
            instructors.append((object.role, object.senior))

        return instructors
    
    @classmethod
    def get_senior_queryset_after_date(cls, senior: Senior, date: date):
        queryset = cls.objects.filter(
            senior=senior,
            night__date__gte=date,  # trainingnight date is before date
        )
        return queryset