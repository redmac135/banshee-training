from django import forms
from django.core.exceptions import ValidationError

import re

from .models import Activity, Lesson, TrainingNight, EmptyLesson, Teach


# Forms to edit Teach Instances
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

    def clean(self):
        cleaned_data = self.cleaned_data
        p1_choice = self.cleaned_data.get("p1_choice")
        p2_choice = self.cleaned_data.get("p2_choice")
        p3_choice = self.cleaned_data.get("p3_choice")

        if len(p1_choice + p2_choice + p3_choice) <= 0:
            raise ValidationError(
                {"p1_choice": "Please select at least 1 timeslot to assign lesson."}
            )

        return cleaned_data

    def get_teach_list(self):
        data = self.cleaned_data
        night_id = self.night_id
        instance: TrainingNight = TrainingNight.objects.get(id=night_id)

        teach_list = []

        p1_teachs = instance.p1.lessons.all()
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
    EOCODE_REGEX = re.compile("^[a-zA-Z][a-zA-Z0-9_.-]\d\d\.\d\d$")

    eocode = forms.CharField(
        max_length=64, widget=forms.TextInput(attrs={"placeholder": "M000.00"})
    )
    title = forms.CharField(max_length=256, required=False)

    def get_content_instance(self):
        data = self.cleaned_data

        return Lesson.create(data["eocode"], data["title"])

    def clean(self):
        cleaned_data = super().clean()
        eocode = cleaned_data.get("eocode")
        title = cleaned_data.get("title")

        if eocode:
            if not self.EOCODE_REGEX.match(eocode):
                raise ValidationError(
                    {"eocode": "Please enter the eocode in the format M000.00"}
                )
        
        if not title:
            tmp_title = Lesson.get_title(eocode)
            if tmp_title == False:
                raise ValidationError({"title": "Lesson title not found, please enter manually."})
            else:
                cleaned_data["title"] = tmp_title

        return cleaned_data


class ActivityTeachForm(BaseTeachForm):
    title = forms.CharField(max_length=256, required=True)

    def get_content_instance(self):
        data = self.cleaned_data

        return Activity.create(data["title"])
