from django.db import models
from django.contrib.auth.models import User

# Managing People
class Level(models.Model):
    name = models.CharField(max_length=2)

    def __str__(self):
        return self.name

class Cadet(models.Model):
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    rank = models.IntegerField()
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.level + " " + self.firstname + " " + self.lastname

    def get_cadets_by_level(self, level):
        return self.objects.filter(level=level)
    class Meta:
        ordering = ['level', 'rank']
        abstract = True

class Senior(Cadet):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)

    def get_choice_tuple():
        tuples = []
        for senior in Senior.objects.filter(user__isnull=True):
            tuples.append((str(senior.id), str(senior)))
        return tuples

class Junior(Cadet):

    def create_cadet(firstname, lastname, rank, level):
        cadet = Junior.objects.create(
            firstname=firstname, 
            lastname=lastname, 
            rank=rank, 
            level=level
        )
        for po in PO.get_pos():
            MapPORequirement.objects.create(cadet, po, 0)
        return cadet
    

# Managing Training POs
class PO(models.Model):
    number = models.IntegerField()

    def __str__(self):
        return "PO" + str(self.number)

    def get_pos():
        return PO.objects.all()

class MapPORequirement(models.Model):
    cadet = models.ForeignKey(Junior, on_delete=models.CASCADE)
    PO = models.ForeignKey(PO, on_delete=models.CASCADE)
    amount = models.IntegerField

    def __str__(self):
        return self.cadet + " " + self.PO

    def get_cadet_qualifications(cadet):
        return MapPORequirement.objects.filter(cadet=cadet)

# Lessons
class Lesson(models.Model):
    title = models.CharField(max_length=256)
    eocode = models.CharField(max_length=11)
    po = models.ForeignKey(PO, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.eocode

class Teach(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True)
    level = models.ManyToManyField(Level)

    def __str__(self):
        if MapSeniorAssignment.get_ic(self.lesson):
            return MapSeniorAssignment.get_ic(self.lesson).senior + " " + self.lesson
        else:
            return "No IC " + self.lesson
    
    def assign_senior(self, senior, role):
        # TODO: make sure there is only 1 IC per lesson
        MapSeniorAssignment.objects.create(senior, self, role)

class MapCadetAttendance(models.Model):
    cadet = models.ForeignKey(Junior, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Teach, on_delete=models.CASCADE)

class MapSeniorAssignment(models.Model):
    senior = models.ForeignKey(Senior, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Teach, on_delete=models.CASCADE)
    role = models.IntegerField(
            help_text='0->ic, 1->mod/adi',
            choices=((0, 'ic'), (1, 'mod/adi'))
        )

    def get_ic(lesson):
        if MapSeniorAssignment.objects.filter(lesson=lesson, role=0).exists():
            return MapSeniorAssignment.objects.get(lesson=lesson, role=0)
        else:
            return False

# Training Nights
class TrainingPeriod(models.Model):
    lessons = models.ManyToManyField(Teach)

class TrainingNight(models.Model):
    date = models.DateField()
    p1 = models.OneToOneField(TrainingPeriod, related_name='periodone', on_delete=models.SET_NULL, null=True)
    p2 = models.OneToOneField(TrainingPeriod, related_name='periodtwo', on_delete=models.SET_NULL, null=True)
    p3 = models.OneToOneField(TrainingPeriod, related_name='periodthree', on_delete=models.SET_NULL, null=True)
    excused = models.ManyToManyField(Senior)

    class Meta:
        ordering = ['-date']