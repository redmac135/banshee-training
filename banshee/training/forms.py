from django import forms
from django.forms import inlineformset_factory, ModelForm, BaseInlineFormSet
from django.db.models.fields import BLANK_CHOICE_DASH
from django.core.exceptions import ValidationError

from emails.models import Email

import re

from .models import (
    Activity,
    GenericLesson,
    Lesson,
    Senior,
    TrainingNight,
    EmptyLesson,
    Teach,
    MapSeniorTeach,
    MapSeniorNight,
)
from users.models import TrainingSetting


# Edit Senior Form
class AssignTeachForm(ModelForm):
    BLANK_CHOICE_SENIOR = [("", "Senior")]
    BLANK_CHOICE_DASH = BLANK_CHOICE_DASH

    # List attribute for datalist in template
    role = forms.CharField(
        max_length=32, widget=forms.TextInput(attrs={"list": "role_datalist"})
    )
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

        senior_assignment_setting = TrainingSetting.get_senior_assignment()

        if senior_assignment_setting:
            if senior_instance.permission_level > 2:
                raise ValidationError({"senior": "You can't assign this senior."})
        else:
            if senior_instance.permission_level > 1:
                raise ValidationError({"senior": "You can't assign this senior."})

        return cleaned_data

    def save(self, commit: bool = True):
        super(AssignTeachForm, self).save(commit)
        cleaned_data = self.cleaned_data
        Email.send_teach_assignment_email(
            user=cleaned_data.get("senior").user,
            teach=self.parent_instance,
            role=cleaned_data.get("role"),
        )


class AssignNightForm(AssignTeachForm):
    def __init__(self, *args, night_id, senior_choices, parent_instance, **kwargs):
        ModelForm.__init__(self, *args, **kwargs)

        self.night_id = night_id
        self.parent_instance = parent_instance
        self.fields["senior"].choices = (
            self.BLANK_CHOICE_SENIOR + self.BLANK_CHOICE_DASH + senior_choices
        )

    class Meta:
        model = MapSeniorNight
        fields = ["role", "senior"]

    def save(self, commit: bool = True):
        ModelForm.save(self, commit)
        cleaned_data = self.cleaned_data
        Email.send_night_assignment_email(
            user=cleaned_data.get("senior").user,
            night=self.parent_instance,
            role=cleaned_data.get("role"),
        )


AssignTeachFormset = inlineformset_factory(
    Teach, MapSeniorTeach, form=AssignTeachForm, extra=2
)


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
    EXTENDED_EOCODE_REGEX = re.compile(
        "^EO [a-zA-Z][a-zA-Z0-9_.-]\d\d\.\d\d$"
    )  # A code including the EO at the beginning

    eocode = forms.CharField(
        max_length=64, widget=forms.TextInput(attrs={"placeholder": "M000.00"})
    )
    title = forms.CharField(max_length=256, required=False)

    def get_content_instance(self):
        data = self.cleaned_data

        return Lesson.create(data["eocode"], data["title"])

    def clean(self):
        cleaned_data = super(LessonTeachForm, self).clean()
        eocode = cleaned_data.get("eocode")
        title = cleaned_data.get("title")

        if eocode:
            # Remove "EO " from "EO M000.00" if it is in that form
            if self.EXTENDED_EOCODE_REGEX.match(eocode):
                cleaned_data["eocode"] = eocode[3:]
                eocode = eocode[3:]
            # Don't need to leave if-statement as the resulting string should be in form "M000.00"
            if not self.EOCODE_REGEX.match(eocode):
                raise ValidationError(
                    {
                        "eocode": "Please enter the eocode in the format M000.00 or EO M000.00"
                    }
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

class GenericLessonTeachForm(BaseTeachForm):
    topic = forms.CharField(max_length=256, required=True)
    title = forms.CharField(max_length=256, required=True)

    def get_content_instance(self):
        data = self.cleaned_data

        return GenericLesson.create(data["topic"], data["title"])


class TeachPlanForm(ModelForm):
    URL_REGEX = re.compile(
        "^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$",
        re.IGNORECASE,
    )

    def __init__(self, teach_id: int, *args, **kwargs):
        super(TeachPlanForm, self).__init__(*args, **kwargs)

        self.instance = Teach.get_by_teach_id(teach_id)

    class Meta:
        model = Teach
        fields = ["plan"]

    def clean(self):
        cleaned_data = self.cleaned_data
        plan = cleaned_data.get("plan")

        if plan:
            if not self.URL_REGEX.match(plan):
                raise ValidationError({"plan": "Please enter a Valid URL."})

    def save(self, commit=False):
        cleaned_data = self.cleaned_data
        plan = cleaned_data.get("plan")

        self.instance.update_plan(plan)
