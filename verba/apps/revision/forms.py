from django import forms


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
