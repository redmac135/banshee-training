from django.db import models

# Create your models here.


# Managing People
class Cadet(models.Model):
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    rank = models.IntegerField()
    level = models.IntegerField()

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
        return 

# Managing Training POs
class PO(models.Model):
    number = models.IntegerField()

class MapPORequirement(models.Model):
    cadet = models.ForeignKey(Junior)
    PO = models.ForeignKey(PO)
    amount = models.IntegerField