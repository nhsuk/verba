from django import forms

from .constants import BRANCH_PARTS_SEPARATOR


class BaseForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(BaseForm, self).__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class NewRevisionForm(BaseForm):
    title = forms.CharField(max_length=30)

    def __init__(self, *args, **kwargs):
        self.revision_manager = kwargs.pop('revision_manager')
        super(NewRevisionForm, self).__init__(*args, **kwargs)

    def clean_title(self):
        """
        Raises Error if `BRANCH_PARTS_SEPARATOR` in title.
        """
        title = self.cleaned_data['title']
        if BRANCH_PARTS_SEPARATOR in title:
            raise forms.ValidationError("Char '{}' not allowed".format(BRANCH_PARTS_SEPARATOR))
        return title

    def save(self, creator):
        title = self.cleaned_data['title']
        return self.revision_manager.create(title, creator)
