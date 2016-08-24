from django.shortcuts import redirect
from django.views.generic.base import TemplateResponseMixin, ContextMixin
from django.views.generic.edit import ProcessFormView, FormMixin
from django.views.generic import View, TemplateView, FormView
from django.http import Http404
from django.contrib import messages
from django.core.urlresolvers import reverse

from .models import RevisionManager
from .forms import NewRevisionForm, ContentForm, SendFor2iForm
from .exceptions import RevisionNotFoundException


class RevisionMixin(object):
    @property
    def revision_manager(self):
        if not hasattr(self, '_revision_manager'):
            self._revision_manager = RevisionManager(self.request.user.token)
        return self._revision_manager


class RevisionDetailMixin(RevisionMixin):
    def get_revision(self):
        if not hasattr(self, '_revision'):
            try:
                self._revision = self.revision_manager.get(self.kwargs['revision_id'])
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
        return reverse('revision:editor', kwargs={'revision_id': self.revision.id})


class BaseRevisionDetailMixin(RevisionDetailMixin, TemplateResponseMixin, ContextMixin):
    template_name = None
    page_type = None

    def dispatch(self, *args, **kwargs):
        # redirect to list if logged-in user doesn't have access to revision
        revision = self.get_revision()
        if self.request.user.pk not in revision.assignees:
            messages.error(self.request, "You can't view the revision as it's not assigned to you.")
            return redirect('revision:list')

        return super(BaseRevisionDetailMixin, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BaseRevisionDetailMixin, self).get_context_data(**kwargs)
        context['revision'] = self.get_revision()
        context['page_type'] = self.page_type
        return context


class Editor(BaseRevisionDetailMixin, View):
    http_method_names = ['get']
    template_name = 'revision/detail-editor.html'
    page_type = 'editor'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class EditFile(BaseRevisionDetailMixin, FormMixin, ProcessFormView):
    form_class = ContentForm
    template_name = 'revision/detail-editor.html'
    page_type = 'editor'

    def get_revision_file(self):
        if not hasattr(self, '_revision_file'):
            revision = self.get_revision()
            try:
                self._revision_file = revision.get_file(self.kwargs['file_path'])
            except RevisionNotFoundException as e:
                raise Http404(e)

        return self._revision_file

    def get_form_kwargs(self):
        kwargs = super(EditFile, self).get_form_kwargs()
        kwargs['revision_file'] = self.get_revision_file()
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'File changed.')
        return super(EditFile, self).form_valid(form)

    def get_success_url(self):
        return self.get_revision_file().get_absolute_url()


class SendFor2i(BaseRevisionDetailMixin, FormMixin, ProcessFormView):
    form_class = SendFor2iForm
    template_name = 'revision/send-for-2i.html'

    def get_form_kwargs(self):
        kwargs = super(SendFor2i, self).get_form_kwargs()
        kwargs['revision'] = self.get_revision()
        return kwargs

    def form_valid(self, form):
        new_assignee = form.save()
        messages.success(self.request, 'Revision sent for 2i and assigned to {}'.format(new_assignee))
        return super(SendFor2i, self).form_valid(form)

    def get_success_url(self):
        return reverse('revision:list')
