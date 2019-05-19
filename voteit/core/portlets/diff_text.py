from __future__ import unicode_literals

from arche.portlets import PortletType
from pyramid.renderers import render
from pyramid.traversal import resource_path
from repoze.catalog.query import Any
from repoze.catalog.query import Eq
from repoze.catalog.query import NotAny

from voteit.core.models.interfaces import IDiffText
from voteit.core import _
from voteit.core.security import ADD_PROPOSAL
from voteit.core.security import EDIT


class DiffTextPortlet(PortletType):
    name = "diff_text"
    title = _("Proposed text body")
    tpl = "voteit.core:templates/portlets/diff_text.pt"

    def render(self, context, request, view, **kwargs):
        if request.meeting:
            diff_text = IDiffText(context)
            paragraphs = diff_text.get_paragraphs()
            if paragraphs or request.is_moderator:
                tags_count = self.count_tags(context, request, diff_text.hashtag, len(paragraphs))
                response = {'title': self.title,
                            'portlet': self.portlet,
                            'diff_text': diff_text,
                            'paragraphs': paragraphs,
                            'tags_count': tags_count,
                            'collapsible_limit': diff_text.get_collapsible_limit(),
                            'can_add': request.has_permission(ADD_PROPOSAL, context),
                            'can_edit': request.has_permission(EDIT, context),
                            'view': view}
                return render(self.tpl,
                              response,
                              request = request)

    def count_tags(self, context, request, base_tag, num):
        results = {}
        query = Eq('path', resource_path(context)) & Eq('type_name', 'Proposal')
        query &= NotAny('workflow_state', ['retracted', 'unhandled'])
        cquery = request.root.catalog.query
        for i in range(1, num+1):
            tag = "%s-%s" % (base_tag, i)
            res = cquery(query & Any('tags', [tag]))[0]
            results[tag] = res.total
        return results


def includeme(config):
    config.add_portlet(DiffTextPortlet)
