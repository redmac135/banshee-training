from django import forms

from .models import Activity, Lesson, TrainingNight, EmptyLesson, Teach

# Group 1 is rendered seperately from group 2
class BaseTeachForm(forms.Form):
    LIST_FIELDS = ("p1_choice", "p2_choice", "p3_choice")

    p1_choice = forms.MultipleChoiceField(
        choices=[("", "")], widget=forms.CheckboxSelectMultiple, required=False
    )
    p2_choice = forms.MultipleChoiceField(
        choices=[("", "")], widget=forms.CheckboxSelectMultiple, required=False
    )
    p3_choice = forms.MultipleChoiceField(
        choices=[("", "")], widget=forms.CheckboxSelectMultiple, required=False
    )
    location = forms.CharField(max_length=64)

    def __init__(self, levels: list, night_id: int, *args, **kwargs):
        super(BaseTeachForm, self).__init__(*args, **kwargs)

        level_choices = []
        for i, level in enumerate(levels, 0):
            level_choices.append((i, level.name))

        self.fields["p1_choice"].choices = level_choices
        self.fields["p2_choice"].choices = level_choices
        self.fields["p3_choice"].choices = level_choices

        self.night_id = night_id

    def get_teach_list(self):
        data = self.cleaned_data
        night_id = self.night_id
        instance: TrainingNight = TrainingNight.objects.get(id=night_id)

        teach_list = []

        p1_teachs = instance.p1.lessons.all()
        print(list(p1_teachs))
        for index in data["p1_choice"]:
            teach_list.append(p1_teachs[int(index)])

        p2_teachs = instance.p2.lessons.all()
        for index in data["p2_choice"]:
            teach_list.append(p2_teachs[int(index)])

        p3_teachs = instance.p3.lessons.all()
        for index in data["p3_choice"]:
            teach_list.append(p3_teachs[int(index)])

        return teach_list

    def get_content_instance(self):
        return EmptyLesson.create()

    def save(self):
        teach_list = self.get_teach_list()
        content = self.get_content_instance()
        location = self.cleaned_data["location"]
        lesson_id = Teach.get_next_lesson_id()

        for teach in teach_list:
            teach.change_content(content)
            teach.location = location
            teach.lesson_id = lesson_id
            teach.save()

    def content_fields(self):
        return [field for field in self if not field.name in self.LIST_FIELDS]

    def slot_fields(self):
        return [field for field in self if field.name in self.LIST_FIELDS]


class LessonTeachForm(BaseTeachForm):
    eocode = forms.CharField(max_length=64, widget=forms.TextInput(attrs={"placeholder": "M000.00"}))
    eocode.group = 1
    title = forms.CharField(max_length=256)
    title.group = 1

    def get_content_instance(self):
        data = self.cleaned_data

        return Lesson.create(data["eocode"], data["title"])


class ActivityTeachForm(BaseTeachForm):
    title = forms.CharField(max_length=256)
    title.group = 1

    def get_content_instance(self):
        data = self.cleaned_data

        return Activity.create(data["title"])
