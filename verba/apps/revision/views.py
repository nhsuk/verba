from django.views.generic import TemplateView, FormView
from django.contrib import messages
from django.core.urlresolvers import reverse

from .models import RevisionManager
from .forms import NewRevisionForm


class RevisionMixin(object):
    @property
    def revision_manager(self):
        if not hasattr(self, '_revision_manager'):
            self._revision_manager = RevisionManager(self.request.user.token)
        return self._revision_manager


class RevisionList(RevisionMixin, TemplateView):
    http_method_names = ['get']
    template_name = 'revision/list.html'

    def get_context_data(self, **kwargs):
        context = super(RevisionList, self).get_context_data(**kwargs)
        context['revisions'] = self.revision_manager.get_all()
        return context


class NewRevision(RevisionMixin, FormView):
    form_class = NewRevisionForm
    template_name = 'revision/new.html'

    def get_form_kwargs(self):
        kwargs = super(NewRevision, self).get_form_kwargs()
        kwargs['revision_manager'] = self.revision_manager
        return kwargs

    def form_valid(self, form):
        self.revision = form.save(self.request.user.pk)
        messages.success(self.request, 'Revision created.')
        return super(NewRevision, self).form_valid(form)

    def get_success_url(self):
        return reverse('revision:list')
