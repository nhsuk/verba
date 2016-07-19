from django import forms


class NewRevisionForm(forms.Form):
    title = forms.CharField(max_length=30)

    def __init__(self, *args, **kwargs):
        self.revision_manager = kwargs.pop('revision_manager')
        super(NewRevisionForm, self).__init__(*args, **kwargs)

    def save(self):
        title = self.cleaned_data['title']
        return self.revision_manager.create(title)


class ContentForm(forms.Form):
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


class SendForApprovalForm(forms.Form):
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
