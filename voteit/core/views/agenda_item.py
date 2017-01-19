from arche.views.base import BaseView
#from betahaus.pyracont.factories import createSchema
#from pyramid.renderers import render
#from pyramid.response import Response
#from pyramid.traversal import find_interface
from pyramid.traversal import resource_path
#from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from voteit.core import VoteITMF as _
#from voteit.core.helpers import ajax_options
#from voteit.core.helpers import generate_slug
from voteit.core.models.interfaces import IAgendaItem
#from voteit.core.models.interfaces import IDiscussionPost
#from voteit.core.models.interfaces import IProposal
#from voteit.core.models.schemas import button_add
#from voteit.core.security import MODERATE_MEETING
from voteit.core import security
from voteit.core.fanstaticlib import unread_js
#from voteit.core.views.base_view import BaseView


class AgendaItemView(BaseView):

    def next_ai(self):
        """ Return next qgenda item if there is one.
        """
        query = u"path == '%s' and type_name == 'AgendaItem'" % resource_path(self.context.__parent__)
        query += u" and order > %s" % self.context.get_field_value('order')
        query += u" and workflow_state in any(['ongoing', 'upcoming', 'closed'])"
        for ai in self.catalog_query(query, resolve = True, limit = 1, sort_index='order'):
            return ai

    def previous_ai(self):
        """ Return previous agenda item if there is one.
        """
        query = u"path == '%s' and type_name == 'AgendaItem'" % resource_path(self.context.__parent__)
        query += u" and order < %s" % self.context.get_field_value('order')
        query += u" and workflow_state in any(['ongoing', 'upcoming', 'closed'])"
        for ai in self.catalog_query(query, resolve = True, limit = 1, sort_index='order', reverse = True):
            return ai

    def __call__(self):
        unread_js.need()
        return {}


class AIToggleBlockView(BaseView):

    def __call__(self):
        """ Toggle wether discussion or proposals are allowed. """
        discussion_block = self.request.GET.get('discussion_block', None)
        proposal_block = self.request.GET.get('proposal_block', None)
        if discussion_block is not None:
            val = bool(int(discussion_block))
            self.context.set_field_value('discussion_block', val)
        if proposal_block is not None:
            val = bool(int(proposal_block))
            self.context.set_field_value('proposal_block', val)
        self.flash_messages.add(_(u"Status changed - note that workflow state also matters."))
        url = self.request.resource_url(self.context)
        if self.request.referer:
            url = self.request.referer
         #FIXME: This should be done via javascript instead
        return HTTPFound(location=url)


def includeme(config):
    config.add_view(AgendaItemView,
                    context = IAgendaItem,
                    renderer = "voteit.core:templates/agenda_item.pt",
                    permission = security.VIEW)
    config.add_view(AIToggleBlockView,
                    context = IAgendaItem,
                    name = "_toggle_block",
                    permission = security.MODERATE_MEETING)
