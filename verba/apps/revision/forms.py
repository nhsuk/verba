from django import forms

from .constants import BRANCH_PARTS_SEPARATOR


class NewRevisionForm(forms.Form):
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


class ContentForm(forms.Form):
    KNOWN_FIELDS_METADATA = {
        'title': {
            'ordering': '1',
            'type': {
                'field': forms.CharField,
                'kwargs': {}
            }
        }
    }

    @classmethod
    def get_field_metadata(cls, field_name):
        field_metadata = cls.KNOWN_FIELDS_METADATA.get(field_name)
        if not field_metadata:
            field_metadata = {
                'ordering': field_name,
                'type': {
                    'field': forms.CharField,
                    'kwargs': {
                        'widget': forms.Textarea(attrs={'rows': 10, 'cols': 110})
                    }
                }
            }
        return field_metadata

    def __init__(self, *args, **kwargs):
        self.revision_file = kwargs.pop('revision_file')

        super(ContentForm, self).__init__(*args, **kwargs)

        fields_data = []
        for field_name, field_value in self.revision_file.get_content_items().items():
            field_metadata = self.get_field_metadata(field_name)
            fields_data.append(
                (field_name, field_value, field_metadata)
            )

        fields_data = sorted(fields_data, key=lambda x: x[2]['ordering'])

        for name, value, metadata in fields_data:
            kwargs = metadata['type'].get('kwargs', {})
            kwargs['initial'] = value
            self.fields[name] = metadata['type']['field'](**kwargs)

    def save(self):
        self.revision_file.save_content_items(self.cleaned_data)


class SendFor2iForm(forms.Form):
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 10, 'cols': 50})
    )

    def __init__(self, *args, **kwargs):
        self.revision = kwargs.pop('revision')

        super(SendFor2iForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(SendFor2iForm, self).clean()
        if self._errors:  # skip if there are already some errors
            return cleaned_data

        if not self.revision.is_in_draft():
            raise forms.ValidationError(
                "This revision is not in draft so it can't be submitted for 2i"
            )

        return cleaned_data

    def save(self):
        comment = self.cleaned_data.get('comment')
        if comment:
            self.revision.add_comment(comment)

        return self.revision.move_to_2i()
