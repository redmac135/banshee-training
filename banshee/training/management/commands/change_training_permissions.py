from django.core.management.base import BaseCommand
from training.models import Senior

class Command(BaseCommand):
    help = f'''
        Promotes a senior based on Username
        Standard Instructor: {Senior.STANDARD_INSTRUCTOR}
        Training Manager: {Senior.TRAINING_MANAGER}
    '''

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Indicates the username of the targeted user")
        parser.add_argument("permission", type=int, help="The permission level for the senior")

    def handle(self, *args, **kwargs):
        username = kwargs.get("username")
        permission = kwargs.get("permission")
        instance = Senior.get_by_username(username)
        instance.change_permission(permission)
        self.stdout.write(f"Senior {str(instance)} changed to permission level {permission}")
