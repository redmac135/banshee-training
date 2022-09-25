from django.db import models

# Considered bad practice to import
from users.models import TrainingSetting

# Senior Managers
class SeniorManager(models.Manager):
    # Exclude all officers from senior queryset
    def get_queryset(self):
        return super(SeniorManager, self).get_queryset().filter(permission_level__lte=2)

    def get_by_level(self, level):
        return self.get_queryset().filter(level=level)

    def get_by_id(self, id: int):
        return self.get_queryset().get(id=id)
    
    def get_by_username(self, username: str):
        return self.get_queryset().get(user__username=username)

class InstructorManager(models.Manager):
    def get_queryset(self):
        queryset = super(InstructorManager, self).get_queryset()
        senior_assignment_setting = TrainingSetting.get_senior_assignment()
        if senior_assignment_setting:
            return queryset.filter(permission_level__lte=2)
        else:
            return queryset.filter(permission_level=1)