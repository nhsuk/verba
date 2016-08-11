from django.views.generic import TemplateView

from .models import RevisionManager


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
