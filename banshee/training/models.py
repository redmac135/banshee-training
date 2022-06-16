from django.db import models
from django.contrib.auth.models import User

# Managing People
class Level(models.Model):
    number = models.IntegerField()
    subset = models.CharField(max_length=1, blank=True) # The 'a' in 2a

    def __str__(self):
        return self.name

class Senior(models.Model):
    rank = models.IntegerField()
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.rank + ". " + self.user.last_name + ", " + self.user.first_name

    class Meta:
        ordering = ['level', 'rank']

    def get_juniors_by_level(level):
        return Senior.objects.filter(level=level)

    def get_choice_tuple():
        seniors = Senior.objects.filter(user__isnull=True).values_list('id', 'rank', 'lastname', 'firstname')
        output = []
        for senior in seniors:
            output.append((senior[0], senior[1]+ ". "+senior[2]+", "+senior[3]))
        return tuple(output)

class Junior(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    rank = models.IntegerField()
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.rank + ". " + self.last_name + ", " + self.first_name
    
    class Meta:
        ordering = ['level', 'rank']

    def get_juniors_by_level(level):
        return Junior.objects.filter(level=level)

    def create_cadet(firstname, lastname, rank, level):
        cadet = Junior.objects.create(
            firstname=firstname, 
            lastname=lastname, 
            rank=rank, 
            level=level
        )
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
 
    def get_pos(level):
        queries = {
            1: PO.objects.filter(lev1=True),
            2: PO.objects.filter(lev2=True),
            3: PO.objects.filter(lev3=True),
            4: PO.objects.filter(lev4=True), 
        }
        return queries.get(level)
    
    def get_choice_tuples():
        pos = ((1, 312), (2, 321))
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