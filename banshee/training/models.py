from django.db import models

# Create your models here.


# Managing People
class Level(models.Model):
    name = models.CharField(max_length=2)

class Cadet(models.Model):
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    rank = models.IntegerField()
    level = models.ForeignKey(Level, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['level', 'rank']
        abstract = True

class Senior(Cadet):
    pass

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

    def get_pos():
        return PO.objects.all()

class MapPORequirement(models.Model):
    cadet = models.ForeignKey(Junior, on_delete=models.CASCADE)
    PO = models.ForeignKey(PO, on_delete=models.CASCADE)
    amount = models.IntegerField

    def get_cadet_qualifications(cadet):
        return MapPORequirement.objects.filter(cadet=cadet)

# Lessons
class Lesson(models.Model):
    title = models.CharField(max_length=256)
    eocode = models.CharField(max_length=11)
    po = models.ForeignKey(PO)
    level = models.ForeignKey(Level, on_delete=models.SET_NULL)

class MapCadetAttendance(models.Model):
    cadet = models.ForeignKey(Junior, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)

# Training Nights
class TrainingPeriod(models.Model):
    lessons = models.ManyToManyField(Lesson)

class TrainingNight(models.Model):
    date = models.DateField()
    periodone = models.OneToOneField(TrainingPeriod, on_delete=models.SET_NULL, null=True)
    periodtwo = models.OneToOneField(TrainingPeriod, on_delete=models.SET_NULL, null=True)
    periodthree = models.OneToOneField(TrainingPeriod, on_delete=models.SET_NULL, null=True)