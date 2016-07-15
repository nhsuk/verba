from django.conf import settings
from django.http import Http404
from django.views.generic import TemplateView, FormView

from .models import RevisionManager
from .exceptions import RevisionNotFoundException
from .forms import ContentForm


class RevisionList(TemplateView):
    http_method_names = ['get']
    template_name = 'revision/list.html'

    def get_context_data(self, **kwargs):
        context = super(RevisionList, self).get_context_data(**kwargs)

        revision_manager = RevisionManager(token=settings.VERBA_GITHUB_TOKEN)
        context['revisions'] = revision_manager.get_all()
        return context


class RevisionMixin(object):
    def get_revision(self):
        if not hasattr(self, '_revision'):
            revision_manager = RevisionManager(token=settings.VERBA_GITHUB_TOKEN)

            try:
                self._revision = revision_manager.get_by_name(self.kwargs['revision_name'])
            except RevisionNotFoundException as e:
                raise Http404(e)
        return self._revision


class RevisionDetail(RevisionMixin, TemplateView):
    http_method_names = ['get']
    template_name = 'revision/detail.html'

    def get_context_data(self, **kwargs):
        context = super(RevisionDetail, self).get_context_data(**kwargs)

        context['revision'] = self.get_revision()
        return context


class RevisionFileDetail(RevisionMixin, FormView):
    initial = {}
    form_class = ContentForm

    template_name = 'revision/detail.html'

    def get_revision_file(self):
        if not hasattr(self, '_revision_file'):
            revision = self.get_revision()
            try:
                self._revision_file = revision.get_file_by_path(self.kwargs['file_path'])
            except RevisionNotFoundException as e:
                raise Http404(e)

        return self._revision_file

    def get_form_kwargs(self):
        kwargs = super(RevisionFileDetail, self).get_form_kwargs()
        kwargs['revision_file'] = self.get_revision_file()
        return kwargs

    def form_valid(self, form):
        form.save()
        return super(RevisionFileDetail, self).form_valid(form)

    def get_success_url(self):
        return self.get_revision_file().get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super(RevisionFileDetail, self).get_context_data(**kwargs)

        context.update({
            'revision': self.get_revision(),
            'revision_file': self.get_revision_file()
        })

        return context
