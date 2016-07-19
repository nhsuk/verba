from django.conf import settings
from django.http import Http404
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView, FormView

from .models import RevisionManager
from .exceptions import RevisionNotFoundException
from .forms import ContentForm, NewRevisionForm, SendForApprovalForm


class RevisionMixin(object):
    @property
    def revision_manager(self):
        if not hasattr(self, '_revision_manager'):
            self._revision_manager = RevisionManager(token=settings.VERBA_GITHUB_TOKEN)
        return self._revision_manager


class RevisionDetailMixin(RevisionMixin):
    def get_revision(self):
        if not hasattr(self, '_revision'):
            try:
                self._revision = self.revision_manager.get_by_id(self.kwargs['revision_id'])
            except RevisionNotFoundException as e:
                raise Http404(e)
        return self._revision


class RevisionList(RevisionMixin, TemplateView):
    http_method_names = ['get']
    template_name = 'revision/list.html'

    def get_context_data(self, **kwargs):
        context = super(RevisionList, self).get_context_data(**kwargs)
        context['revisions'] = self.revision_manager.get_all()
        return context


class RevisionDetail(RevisionDetailMixin, TemplateView):
    http_method_names = ['get']
    template_name = 'revision/detail.html'

    def get_context_data(self, **kwargs):
        context = super(RevisionDetail, self).get_context_data(**kwargs)
        context['revision'] = self.get_revision()
        return context


class RevisionFileDetail(RevisionDetailMixin, FormView):
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
        messages.success(self.request, 'File changed.')
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


class NewRevision(RevisionMixin, FormView):
    form_class = NewRevisionForm
    template_name = 'revision/new.html'

    def get_form_kwargs(self):
        kwargs = super(NewRevision, self).get_form_kwargs()
        kwargs['revision_manager'] = self.revision_manager
        return kwargs

    def form_valid(self, form):
        self.revision = form.save()
        messages.success(self.request, 'Revision created.')
        return super(NewRevision, self).form_valid(form)

    def get_success_url(self):
        return self.revision.get_absolute_url()


class SendForApproval(RevisionDetailMixin, FormView):
    form_class = SendForApprovalForm
    template_name = 'revision/send_for_approval.html'

    def get_form_kwargs(self):
        kwargs = super(SendForApproval, self).get_form_kwargs()
        kwargs['revision'] = self.get_revision()
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Revision sent for approval.')
        return super(SendForApproval, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(SendForApproval, self).get_context_data(**kwargs)

        context.update({
            'revision': self.get_revision()
        })

        return context

    def get_success_url(self):
        return reverse('revision:list')
