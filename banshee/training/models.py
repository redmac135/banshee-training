from datetime import datetime, date, timedelta
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from training.managers import managers

from .managers import level_managers, senior_managers

from users.models import TrainingSetting

# Managing People

# Important: users.forms requires senior numbers be unique
class Level(models.Model):
    OFFICER_LEVEL_NUMBER = 7
    OFFICER_LEVEL_NAME = "oo"  # must be 2 characters

    name = models.CharField(max_length=2)
    number = models.IntegerField()

    # Managers
    objects = models.Manager()
    levels = level_managers.LevelManager()
    seniors = level_managers.SeniorManager()
    juniors = level_managers.JuniorManager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    # Not put into a manager as it's only 1 function
    @classmethod
    def get_officer(cls):
        if cls.objects.filter(number=cls.OFFICER_LEVEL_NUMBER).exists():
            return cls.objects.get(number=cls.OFFICER_LEVEL_NUMBER)
        else:
            return cls.objects.create(
                name=cls.MASTER_LEVEL_NAME, number=cls.MASTER_LEVEL_NUMBER
            )


class Senior(models.Model):
    STANDARD_INSTRUCTOR = 1
    TRAINING_MANAGER = 2
    OFFICER = 3
    ADMIN = 4
    PERMISSION_CHOICES = [
        (STANDARD_INSTRUCTOR, "Standard Instructor"),
        (TRAINING_MANAGER, "Training Manager"),
        (OFFICER, "Officer"),
        (ADMIN, "Admin"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True)
    permission_level = models.IntegerField(choices=PERMISSION_CHOICES, default=1)
    discluded_assignment = models.BooleanField(
        default=False
    )  # Should this senior be discluded from assignments

    # Managers
    objects = models.Manager()
    seniors = senior_managers.SeniorManager()
    instructors = senior_managers.InstructorManager()

    def __str__(self):
        return self.user.username

    class Meta:
        ordering = ["level"]

    def get_absolute_url(self):
        return reverse("api-senior", args=[self.pk])

    def is_training(self):
        if self.permission_level >= 2:
            return True
        else:
            return False

    def change_permission(self, permission: int):
        self.permission_level = permission
        return self.save()

    def change_disclude_status(self, status: bool):
        self.discluded_assignment = status
        return self.save()


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

    # Managers
    objects = models.Manager()
    nights = managers.NightManager()

    def get_absolute_url(self):
        return reverse("trainingnight", args=[self.id])

    def get_periods(self):
        return self.trainingperiod_set.all().order_by("order")

    def get_unassigned(self):
        queryset = Senior.seniors.get_assignable_seniors()
        night_assignment_ids = [senior.id for (role, senior) in self.get_assignments()]

        teach_assignment_ids = []
        for period in self.get_periods():
            for teach in period.get_teach_instances():
                teaching_seniors = [
                    senior.id for (role, senior) in teach.get_assignments()
                ]
                teach_assignment_ids.extend(teaching_seniors)

        filtered = queryset.exclude(
            Q(id__in=night_assignment_ids) | Q(id__in=teach_assignment_ids)
        )
        return filtered

    # Convenience Functions
    def get_assignments(self):
        return MapSeniorNight.get_instructors(self)


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
        levels = Level.juniors.all()
        for level in levels:
            Teach.create(level, instance)
        return instance

    @classmethod
    def create_fullact(cls, night, order):
        instance = cls.objects.create(night=night, order=order)
        levels = Level.juniors.all()
        teach_id = Teach.get_next_teach_id()
        for level in levels:
            Teach.create(level, instance, id=teach_id)
        return instance


# Managing Lessons
class PerformanceObjective(models.Model):
    po = models.CharField(max_length=3, unique=True)
    po_title = models.CharField(max_length=256, blank=True, null=True)

    objects = models.Manager()
    objectives = managers.ObjectiveManager()

    def __str__(self):
        return self.po


class Lesson(models.Model):
    po = models.ForeignKey(PerformanceObjective, on_delete=models.SET_NULL, null=True)
    eocode = models.CharField(
        max_length=64, unique=True
    )  # Should be in the format 'M336.04'
    title = models.CharField(max_length=256)

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

        po_instance = PerformanceObjective.objectives.get_or_create(po, po_title)
        instance = cls.objects.create(po=po_instance, eocode=eocode, title=title)
        return instance

    @classmethod
    def get_title(cls, eocode: str):
        if cls.objects.filter(eocode=eocode).exists():
            instance = cls.objects.get(eocode=eocode)
            return instance.title
        return False

    def get_form_initial(self):
        initial = {}
        initial["eocode"] = self.eocode
        initial["title"] = self.title
        return initial

    def change_title(self, title):
        self.title = title
        self.save()

    # This method is for the utils.trainingdayschedule class
    def format_html_block(self, teach, location: str):
        block = f"<p class='tracking-tight leading-none'>Lesson at {location}</p>"
        block += (
            f"<p class='mb-2 font-bold tracking-tight text-clr-5'>{self.eocode}</p>"
        )

        instructors = ""
        for role, instructor in MapSeniorTeach.get_instructors(teach):
            instructors += f"{role}: {instructor}<br>"
        block += f"<p class='font-normal'>{instructors}</p>"

        return block

    def get_content_attributes(self):
        return [("EO Code", self.eocode), ("Title", self.title)]


class Activity(models.Model):
    title = models.CharField(max_length=256, default="Squadron-Organized Event")

    def __str__(self):
        return self.title

    @classmethod
    def create(cls, title: str):
        instance = cls.objects.create(title=title)
        return instance

    def get_form_initial(self):
        initial = {}
        initial["title"] = self.title
        return initial

    # This method is for the utils.trainingdayschedule class
    def format_html_block(self, teach, location: str):
        block = f"<p class='tracking-tight leading-none'>Activity at {location}</p>"
        block += f"<p class='mb-2 font-bold tracking-tight text-clr-5'>{self.title}</p>"

        instructors = ""
        for role, instructor in MapSeniorTeach.get_instructors(teach):
            instructors += f"{role}: {instructor}<br>"
        block += f"<p class='font-normal'>{instructors}</p>"

        return block

    def get_content_attributes(self):
        return [("Title", self.title)]


class GenericLesson(models.Model):
    topic = models.CharField(max_length=255)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.topic + " " + self.title

    @classmethod
    def create(cls, topic: str, title: str):
        instance = cls.objects.create(topic=topic, title=title)
        return instance

    def get_form_initial(self):
        initial = {}
        initial["topic"] = self.topic
        initial["title"] = self.title
        return initial

    def format_html_block(self, teach, location: str):
        block = f"<p class='tracking-tight leading-none'>Lesson at {location}</p>"
        block += f"<p class='mb-2 font-bold tracking-tight text-clr-5'>{self.title}</p>"

        instructors = ""
        for role, instructor in MapSeniorTeach.get_instructors(teach):
            instructors += f"{role}: {instructor}<br>"
        block += f"<p class='font-normal'>{instructors}</p>"

        return block

    def get_content_attributes(self):
        return [("Topic", self.topic), ("Title", self.title)]


# Blank object for empty teach instances
class EmptyLesson(models.Model):
    def __str__(self):
        return "Empty Lesson Placeholder"

    @classmethod
    def create(cls):
        return cls.objects.create()

    @classmethod
    def format_html_block(self, *args, **kwargs):
        return "<div class='text-center h-full font-bold text-lg tracking-tight'>UNASSIGNED</div>"


class Teach(models.Model):
    DEFAULT_LOCATION = "Classroom"
    DEFAULT_CONTENT_CLASS = EmptyLesson
    CONTENT_CLASSES_LIST = [
        (0, Lesson),
        (1, Activity),
        (2, GenericLesson),
    ]
    CONTENT_CLASSES = [x[1] for x in CONTENT_CLASSES_LIST]

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
        return str(self.teach_id) + " " + str(self.content)

    class Meta:
        ordering = ["teach_id", "id"]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    # TODO: Move and create teachids and levels manager
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

        instance = cls.objects.create(
            teach_id=id, period=period, content=content, level=level
        )
        return instance

    @classmethod
    def get_by_teach_id(cls, teach_id):
        instances = cls.objects.filter(teach_id=teach_id)
        if not instances.exists():
            raise ObjectDoesNotExist("Teach ID not Found")
        return instances.first()

    # Get Teach Attrs or Related Data
    def get_absolute_url(self):
        return reverse("teach", args=[self.teach_id])

    def get_night_id(self):
        return self.period.night.id

    def get_date(self):
        return self.period.night.date

    def get_parent_instance(self):
        return self.get_by_teach_id(self.teach_id)

    @classmethod
    def get_neighbour_instances(cls, teach_id):
        return cls.objects.filter(teach_id=teach_id)

    def get_form_slot_initial(self):
        instances = Teach.get_neighbour_instances(self.teach_id)
        positions = instances.values_list("period__order", "level__name")
        night_instance = self.period.night
        levels = Level.juniors.all()

        slot_initial = []

        for num, period in enumerate(night_instance.get_periods(), 1):
            initial = []
            for level in levels:
                if (num, level.name) in positions:
                    initial.append("checked")
                else:
                    initial.append("")
            slot_initial.append(initial)
        return slot_initial

    def can_edit_plan(self, senior: Senior):
        if senior.is_training():
            return True
        instructors = MapSeniorTeach.get_instructors(self)
        allowed_list = [instructor[1] for instructor in instructors]
        if senior in allowed_list:
            return True
        return False

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
        self: Teach = self.get_parent_instance()
        if self.finished == True:
            return "Submitted"

        today = date.today()
        settings = TrainingSetting.create()
        offset = settings.duedateoffset
        teach_date = self.get_date()

        if teach_date < today + timedelta(days=offset):
            return "Missing"
        else:
            return "Not Submitted"

    def get_assignable_seniors(self):
        queryset = Senior.seniors.get_assignable_seniors()
        night_assignment_ids = [
            senior.id for role, senior in self.period.night.get_assignments()
        ]

        teach_assignment_ids = []
        for teach in self.period.get_teach_instances():
            teaching_seniors = [senior.id for (role, senior) in teach.get_assignments()]
            teach_assignment_ids.extend(teaching_seniors)

        filtered = queryset.exclude(
            Q(id__in=night_assignment_ids) | Q(id__in=teach_assignment_ids)
        )
        return filtered

    # Updating Teach Attrs
    def update_plan(self, plan: str):
        self.plan = plan
        if plan == "":
            self.finished = False
        else:
            self.finished = True
        return self.save()

    def change_content(self, content):
        old_content = self.content

        self.content = content
        self.save()

        if type(old_content) == EmptyLesson:
            old_content.delete()

    # managing content
    def get_content_type(self):
        class_name = type(self.content)
        return class_name

    def get_absolute_edit_url(self):
        night_id = self.get_night_id()
        content_class = self.get_content_type()

        # find link to form to render
        for content_tuple in self.CONTENT_CLASSES_LIST:
            if content_tuple[1] == content_class:
                return reverse(
                    "teach-form", args=[night_id, content_tuple[0], self.teach_id]
                )
        return reverse("teach-form", args=[night_id, 0, self.teach_id])

    def get_content_attributes(self):
        self: Teach = self.get_parent_instance()
        content_class = self.get_content_type()

        if content_class in self.CONTENT_CLASSES:
            return content_class.get_content_attributes(self.content)
        return {}

    def format_html_block(self):
        self: Teach = self.get_parent_instance()
        content_class = self.get_content_type()

        if content_class in self.CONTENT_CLASSES + [self.DEFAULT_CONTENT_CLASS]:
            return content_class.format_html_block(self.content, self, self.location)
        return "UNKNOWN CONTENT CLASS NAME"

    def get_form_content_initial(self):
        initial = {}
        initial["location"] = self.location
        content_class = self.get_content_type()

        if content_class in self.CONTENT_CLASSES:
            initial.update(self.content.get_form_initial())

        return initial

    # Convenience Classes
    def get_assignments(self) -> tuple:
        return MapSeniorTeach.get_instructors(self)


class MapSeniorTeach(models.Model):
    IC_ROLE_NAME = "ic"
    DATALIST_SUGGESTIONS = ["IC", "Mod", "ADI"]

    teach = models.ForeignKey(Teach, on_delete=models.CASCADE)
    senior = models.ForeignKey(Senior, on_delete=models.CASCADE)
    role = models.CharField(max_length=32)

    def __str__(self):
        return str(self.teach.teach_id) + " " + str(self.senior)

    # TODO: Create seniorteachs manager
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

    # TODO: change to get_assignments
    @classmethod
    def get_instructors(cls, teach: Teach):
        queryset = cls.get_teach_queryset(teach)

        instructors = []
        for object in queryset:
            instructors.append((object.role, object.senior))

        # Function for sorting
        def role_priority(role: tuple):
            roles = cls.DATALIST_SUGGESTIONS
            # Role[0] is the role in the (role, senior) tuple
            if role[0] in roles:
                return roles.index(role[0])
            else:
                return len(roles) + 1

        # Sorting the list of tuples
        return sorted(instructors, key=role_priority)

    @classmethod
    def get_senior_queryset_after_date(cls, senior: Senior, date: date):
        queryset = cls.objects.filter(
            senior=senior,
            teach__period__night__date__gte=date,  # teach > trainingperiod > trainingnight date is after date
        )
        return queryset


class MapSeniorNight(models.Model):
    DATALIST_SUGGESTIONS = ["Duty NCO", "Floater"]

    night = models.ForeignKey(TrainingNight, on_delete=models.CASCADE)
    senior = models.ForeignKey(Senior, on_delete=models.CASCADE)
    role = models.CharField(max_length=32)

    def __str__(self):
        return self.role + " for " + str(self.night.date) + " " + str(self.senior)

    @classmethod
    def get_night_queryset(cls, night: TrainingNight):
        queryset = cls.objects.filter(night=night)
        return queryset

    # TODO: change to get assignments
    @classmethod
    def get_instructors(cls, night: TrainingNight):
        queryset = cls.get_night_queryset(night)

        instructors = []
        for object in queryset:
            instructors.append((object.role, object.senior))

        # Function for sorting
        def role_priority(role: tuple):
            roles = cls.DATALIST_SUGGESTIONS
            # Role[0] is the role in the (role, senior) tuple
            if role[0] in roles:
                return roles.index(role[0])
            else:
                return len(roles) + 1

        return sorted(instructors, key=role_priority)

    @classmethod
    def get_senior_queryset_after_date(cls, senior: Senior, date: date):
        queryset = cls.objects.filter(
            senior=senior,
            night__date__gte=date,  # trainingnight date is before date
        )
        return queryset
