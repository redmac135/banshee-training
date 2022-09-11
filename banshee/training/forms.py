from django import forms
from django.forms import inlineformset_factory, ModelForm, BaseInlineFormSet
from django.db.models.fields import BLANK_CHOICE_DASH
from django.core.exceptions import ValidationError

from emails.models import Email

import re

from .models import (
    Activity,
    Lesson,
    Senior,
    TrainingNight,
    EmptyLesson,
    Teach,
    MapSeniorTeach,
    MapSeniorNight,
)


# Edit Senior Form
class AssignTeachForm(ModelForm):
    BLANK_CHOICE_SENIOR = [("", "Senior")]
    BLANK_CHOICE_DASH = BLANK_CHOICE_DASH

    role = forms.CharField(max_length=32)
    senior = forms.ChoiceField(choices=[])

    def __init__(self, *args, teach_id, senior_choices, parent_instance, **kwargs):
        super(AssignTeachForm, self).__init__(*args, **kwargs)

        self.teach_id = teach_id
        self.parent_instance = parent_instance
        self.fields["senior"].choices = (
            self.BLANK_CHOICE_SENIOR + self.BLANK_CHOICE_DASH + senior_choices
        )

    class Meta:
        model = MapSeniorTeach
        fields = ["role", "senior"]

    def clean(self):
        cleaned_data = self.cleaned_data
        senior_id = cleaned_data.get("senior")
        senior_instance = Senior.get_by_id(senior_id)
        cleaned_data.update({"senior": senior_instance})

        return cleaned_data

    def save(self, commit: bool = True):
        cleaned_data = self.cleaned_data
        Email.send_assignment_email(
            user=cleaned_data.get("senior").user,
            teach=self.parent_instance,
            role=cleaned_data.get("role"),
        )
        return super(AssignTeachForm, self).save(commit)


AssignTeachFormset = inlineformset_factory(
    Teach, MapSeniorTeach, form=AssignTeachForm, extra=2
)


class AssignNightForm(ModelForm):
    BLANK_CHOICE_SENIOR = [("", "Senior")]
    BLANK_CHOICE_DASH = BLANK_CHOICE_DASH

    role = forms.CharField(max_length=32)
    senior = forms.ChoiceField(choices=[])

    def __init__(self, *args, night_id, senior_choices, **kwargs):
        super(AssignNightForm, self).__init__(*args, **kwargs)

        self.night_id = night_id
        self.fields["senior"].choices = (
            self.BLANK_CHOICE_SENIOR + self.BLANK_CHOICE_DASH + senior_choices
        )

    class Meta:
        model = MapSeniorNight
        fields = ["role", "senior"]

    def clean(self):
        cleaned_data = self.cleaned_data
        senior_id = cleaned_data.get("senior")
        senior_instance = Senior.get_by_id(senior_id)
        cleaned_data.update({"senior": senior_instance})

        return cleaned_data


AssignNightFormset = inlineformset_factory(
    TrainingNight, MapSeniorNight, form=AssignNightForm, extra=2
)


# Forms to edit Teach Instances
class BaseTeachForm(forms.Form):
    PERIOD_FIELD_TEST = re.compile("^p\d_choice$")
    location = forms.CharField(max_length=64)

    def __init__(self, levels: list, night_id: int, *args, **kwargs):
        super(BaseTeachForm, self).__init__(*args, **kwargs)

        level_choices = []
        for i, level in enumerate(levels, 0):
            level_choices.append((i, level.name))

        self.night_id = night_id

        instance = TrainingNight.get(night_id)
        for number, period in enumerate(instance.get_periods(), 1):
            self.fields[f"p{number}_choice"] = forms.MultipleChoiceField(
                choices=level_choices,
                widget=forms.CheckboxSelectMultiple,
                required=False,
            )

    def clean(self):
        cleaned_data = self.cleaned_data

        fields = cleaned_data.keys()
        test = re.compile("^p\d_choice$")
        period_fields = [field for field in fields if test.match(field)]

        length = 0
        for period_field in period_fields:
            length += len(period_field)
        if length <= 0:
            raise ValidationError(
                {"p1_choice": "Please select at least 1 timeslot to assign lesson."}
            )

        return cleaned_data

    def get_teach_list(self):
        data = self.cleaned_data
        night_id = self.night_id
        instance: TrainingNight = TrainingNight.objects.get(id=night_id)

        teach_list = []
        periods = instance.get_periods()

        for number, period in enumerate(periods, 1):
            teachs = period.get_teach_instances()
            for index in data[f"p{number}_choice"]:
                teach_list.append(teachs[int(index)])

        return teach_list

    def get_content_instance(self):
        return EmptyLesson.create()

    def save(self):
        teach_list = self.get_teach_list()
        content = self.get_content_instance()
        location = self.cleaned_data["location"]
        teach_id = Teach.get_next_teach_id()

        self.teach_id = teach_id  # Used for future reference

        for teach in teach_list:
            teach.change_content(content)
            teach.location = location
            teach.teach_id = teach_id
            teach.save()

    def content_fields(self):
        return [field for field in self if not self.PERIOD_FIELD_TEST.match(field.name)]

    def slot_fields(self):
        return [field for field in self if self.PERIOD_FIELD_TEST.match(field.name)]


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
                raise ValidationError(
                    {"title": "Lesson title not found, please enter manually."}
                )
            else:
                cleaned_data["title"] = tmp_title

        return cleaned_data


class ActivityTeachForm(BaseTeachForm):
    title = forms.CharField(max_length=256, required=True)

    def get_content_instance(self):
        data = self.cleaned_data

        return Activity.create(data["title"])
