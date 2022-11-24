from django import forms
from django.core.validators import validate_slug, EMPTY_VALUES


class CommaSeparatedCharField(forms.Field):
    description = "Command Seperated String"

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop("token", ",")
        super(CommaSeparatedCharField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return []

        value = [item.strip() for item in value.split(self.token) if item.strip()]

        return list(set(value))

    def clean(self, value):
        """
        Check that the field contains one or more 'comma-separated' emails
        and normalizes the data to a list of the email strings.
        """
        value = self.to_python(value)

        if value in EMPTY_VALUES and self.required:
            raise forms.ValidationError("This field is required.")

        for string in value:
            try:
                validate_slug(string)
            except forms.ValidationError:
                raise forms.ValidationError("'%s' is not a valid slug." % string)
        return value

    def prepare_value(self, value):
        if value in EMPTY_VALUES:
            return None
        return ", ".join([str(s) for s in value])
