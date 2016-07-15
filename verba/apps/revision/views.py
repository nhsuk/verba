from django.conf import settings
from django.views.generic import TemplateView

from .models import RevisionManager


class RevisionList(TemplateView):
    http_method_names = ['get']
    template_name = 'revision/list.html'

    def get_context_data(self, **kwargs):
        context = super(RevisionList, self).get_context_data(**kwargs)

        revision_manager = RevisionManager(token=settings.VERBA_GITHUB_TOKEN)
        context['revisions'] = revision_manager.get_all()
        return context
