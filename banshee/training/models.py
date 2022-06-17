from django.db import models
from django.contrib.auth.models import User

# Managing People
class Level(models.Model):
    number = models.IntegerField()
    subset = models.CharField(max_length=1, blank=True) # The 'a' in 2a

    def __str__(self):
        return str(self.number) + " " + self.subset

class Senior(models.Model):
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
    def get_choice_tuple(cls):
        seniors = cls.objects.filter(user__isnull=True).values_list('id', 'rank', 'last_name', 'first_name')
        output = []
        for senior in seniors:
            output.append((senior[0], senior[1]+ ". "+senior[2]+", "+senior[3]))
        return tuple(output)

class Junior(models.Model):
    RANKS = (
        (0, 'cdt'),
        (1, 'lac'),
        (2, 'cpl'),
        (3, 'fcpl'),
        (4, 'sgt'),
        (5, 'fsgt'),
        (6, 'wo2'),
        (7, 'wo1')
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    rank = models.IntegerChoices(choices = RANKS)
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.rank + ". " + self.last_name + ", " + self.first_name
    
    class Meta:
        ordering = ['level', 'rank']

    @classmethod
    def by_level(cls, level):
        return cls.objects.filter(level=level)

    @classmethod
    def create(cls, first_name, last_name, rank, level):
        cadet = cls(
            first_name=first_name, 
            last_name=last_name, 
            rank=rank, 
            level=level
        )
        cadet.save()
        for po in PO.get_pos(level.number):
            MapPORequirement.objects.create(cadet, po, 0)
        return cadet
    
# Managing Training POs
class PO(models.Model):
    number = models.IntegerField() # 2 digit number at the end of PO
    lev1 = models.BooleanField() # does it apply to this level?
    lev2 = models.BooleanField()
    lev3 = models.BooleanField()
    lev4 = models.BooleanField()

    def __str__(self):
        return "PO" + str(self.number)
 
    @classmethod
    def get_pos(cls, level):
        queries = {
            1: cls.objects.filter(lev1=True),
            2: cls.objects.filter(lev2=True),
            3: cls.objects.filter(lev3=True),
            4: cls.objects.filter(lev4=True), 
        }
        return queries.get(level)
    
    @classmethod
    def get_choice_tuples(cls):
        pos = cls.objects.all()
        output = []
        for po in pos:
            output.append((po[0], f"PO X{str(po[1])}"))
        return tuple(output)

class MapPORequirement(models.Model):
    cadet = models.ForeignKey(Junior, on_delete=models.CASCADE)
    PO = models.ForeignKey(PO, on_delete=models.CASCADE)
    amount = models.IntegerField

    def __str__(self):
        return self.cadet + " " + self.PO

    @classmethod
    def get_cadet_qualifications(cls, cadet):
        return cls.objects.filter(cadet=cadet)

# Lessons
class Lesson(models.Model):
    title = models.CharField(max_length=256)
    eocode = models.CharField(max_length=11)
    po = models.ForeignKey(PO, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.eocode

class Teach(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True)
    levels = models.ManyToManyField(Level)
    cadets = models.ManyToManyField(Junior)

    def __str__(self):
        if MapSeniorAssignment.get_ic(self.lesson):
            return MapSeniorAssignment.get_ic(self.lesson).senior + " " + self.lesson
        else:
            return "No IC " + self.lesson
    
    def assign_senior(self, senior, role):
        # TODO: make sure there is only 1 IC per lesson
        MapSeniorAssignment.objects.create(senior, self, role)

class MapSeniorAssignment(models.Model):
    ROLES = (
        (0, 'ic'),
        (1, 'mod')
    )
    senior = models.ForeignKey(Senior, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Teach, on_delete=models.CASCADE)
    role = models.IntegerChoices(
            help_text='0->ic, 1->mod/adi',
            choices=ROLES
        )

    def __str__(self):
        return self.role_to_string(self.role) + " " + self.senior + " " + self.lesson
    
    @classmethod
    def role_to_string(cls, role: int):
        return cls.ROLES[role]

    @classmethod
    def get_ic(cls, lesson):
        if cls.objects.filter(lesson=lesson, role=0).exists():
            return cls.objects.get(lesson=lesson, role=0)
        else:
            return False

# Training Nights
class TrainingPeriod(models.Model):
    lessons = models.ManyToManyField(Teach)

    def __str__(self):
        if self.periodone:
            return self.periodone + ' period 1'
        elif self.periodtwo:
            return self.periodtwo + ' period 2'
        elif self.periodthree:
            return self.periodthree + ' period 3'
        return self.pk + ' no training night'
    
    @classmethod
    def create(cls):
        object = cls()
        object.save()
        return object

class TrainingNight(models.Model):
    date = models.DateField()
    p1 = models.OneToOneField(TrainingPeriod, related_name='periodone', on_delete=models.SET_NULL, null=True)
    p2 = models.OneToOneField(TrainingPeriod, related_name='periodtwo', on_delete=models.SET_NULL, null=True)
    p3 = models.OneToOneField(TrainingPeriod, related_name='periodthree', on_delete=models.SET_NULL, null=True)
    cadets = models.ManyToManyField(Junior)
    excused = models.ManyToManyField(Senior)

    def __str__(self):
        return str(self.date)

    class Meta:
        ordering = ['-date']
    
    @classmethod
    def create(cls, date):
        object = cls(
            date = date,
            p1 = TrainingPeriod.create(),
            p2 = TrainingPeriod.create(),
            p3 = TrainingPeriod.create()
        )
        object.save()
        return object

class MapSeniorTrainingNight(models.Model):
    ROLES = (
        (0, 'duty NCO'),
        (1, '2ed duty'),
        (2, 'floater')
    )
    senior = models.ForeignKey(Senior, on_delete=models.CASCADE)
    training_night = models.ForeignKey(TrainingNight, on_delete=models.CASCADE)
    role = models.IntegerChoices(choices=ROLES)

    def __str__(self):
        return self.senior + " " + self.role_to_string(self.role) + " for " + self.training_night
    
    @classmethod
    def role_to_string(cls, role: int):
        return cls.ROLES[role]
