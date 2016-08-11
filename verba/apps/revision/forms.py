from django import forms

from verba_settings import config


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

    def clean(self, *args, **kwargs):
        super(NewRevisionForm, self).clean(*args, **kwargs)

        if self._errors:  # if there are already errors, skip and return immediately
            return

        if len(self.revision_manager.get_all()) >= config.MAX_REVISIONS:
            raise forms.ValidationError(
                'Reached max number of revisions allowed ({})'.format(config.MAX_REVISIONS)
            )

    def save(self):
        title = self.cleaned_data['title']
        return self.revision_manager.create(title)


class ContentForm(BaseForm):
    content = forms.CharField(widget=forms.Textarea(attrs={'rows': 30, 'cols': 100}))

    def __init__(self, *args, **kwargs):
        self.revision_file = kwargs.pop('revision_file')

        initial = kwargs.get('initial', {})
        initial['content'] = self.revision_file.content
        kwargs['initial'] = initial

        super(ContentForm, self).__init__(*args, **kwargs)

    def save(self):
        new_content = self.cleaned_data['content']
        self.revision_file.change_content(new_content)


class SendForApprovalForm(BaseForm):
    title = forms.CharField(max_length=50)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 50}))

    def __init__(self, *args, **kwargs):
        self.revision = kwargs.pop('revision')

        initial = kwargs.get('initial', {})
        initial.update({
            'title': self.revision.title,
            'description': self.revision.description,
        })
        kwargs['initial'] = initial

        super(SendForApprovalForm, self).__init__(*args, **kwargs)

    def save(self):
        title = self.cleaned_data['title']
        description = self.cleaned_data['description']

        self.revision.send_for_approval(title, description)


class DeleteRevisionForm(BaseForm):
    def __init__(self, *args, **kwargs):
        self.revision = kwargs.pop('revision')
        super(DeleteRevisionForm, self).__init__(*args, **kwargs)

    def save(self):
        self.revision.delete()
