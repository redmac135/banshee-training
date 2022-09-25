from django.db import models

# Level Managers
class LevelManager(models.Manager):
    def get_by_number(self, number: int):
        return self.get(number=number)

class JuniorManager(models.Manager):
    def get_queryset(self):
        return super(JuniorManager, self).get_queryset().filter(number__lte=4, number__gte=1)

class SeniorManager(models.Manager):
    def get_queryset(self):
        return super(SeniorManager, self).get_queryset().filter(number__lte=6, number__gte=5)
    
    def get_choices(self):
        queryset = self.get_queryset()
        return [(level.number, level.name) for level in queryset]