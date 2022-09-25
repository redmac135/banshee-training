from django.db import models

# Night Managers
class NightManager(models.Manager):
    def get_by_date(self, date):
        return self.get_queryset().get(date=date)


class ObjectiveManager(models.Manager):
    def get_or_create(self, po: str, po_title: str):
        if self.filter(po=po).exists():
            return self.get(po=po)
        else:
            instance = self.create(po=po, po_title=po_title)
            return instance
