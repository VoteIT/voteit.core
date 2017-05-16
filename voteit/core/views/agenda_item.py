from arche.views.base import BaseView
from pyramid.httpexceptions import HTTPFound

from voteit.core import _
from voteit.core import security
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.security import VIEW


class AgendaItemView(BaseView):

    def next_ai(self):
        """ Return next agenda item if there is one.
            This may hide the next button if there are hidden agenda items
        """
        return self._get_sibbling_ai(1)

    def previous_ai(self):
        """ Return previous agenda item if there is one.
        """
        return self._get_sibbling_ai(-1)

    def _get_sibbling_ai(self, pos):
        meeting = self.request.meeting
        m_order = tuple(meeting.order)
        ai_count = len(m_order)
        try:
            this_pos = meeting.order.index(self.context.__name__)
        except ValueError:
            return
        #only try a few times - we don't want to iterate through the whole meeting
        # if there's lots of hidden Agenda items.
        for obj_pos in range(this_pos+pos, this_pos+(pos*5), pos):
            if obj_pos < 0 or obj_pos > ai_count:
                return
            try:
                obj = meeting[m_order[obj_pos]]
            except (KeyError, IndexError):
                return
            if not IAgendaItem.providedBy(obj):
                continue
            if self.request.has_permission(VIEW, obj):
                return obj

    def __call__(self):
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
