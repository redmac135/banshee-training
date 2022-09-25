from django.db import models

# Night Managers
class NightManager(models.Manager):
    def get_by_date(self, date):
        return self.get_queryset().get(date=date)
