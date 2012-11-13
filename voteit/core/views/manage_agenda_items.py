from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.traversal import resource_path
from pyramid.traversal import find_resource
from pyramid.url import resource_url
from repoze.workflow.workflow import WorkflowError

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_edit import BaseEdit
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.agenda_item import AgendaItem


class ManageAgendaItemsView(BaseEdit):
    @view_config(context=IMeeting, name="handle_agenda_items", renderer="templates/handle_agenda_items.pt", permission=security.EDIT)
    def handle_agenda_items(self):
        post = self.request.POST
        if 'cancel' in self.request.POST:
            url = self.request.resource_url(self.context, 'handle_agenda_items')
            return HTTPFound(location = url)

        if 'change' in post:
            state_id = self.request.POST['state_id']
            controls = self.request.POST.items()
            for (k, v) in controls:
                if k == 'ais':
                    ai = self.context[v]
                    try:
                        ai.set_workflow_state(self.request, state_id)
                    except WorkflowError, e:
                        self.api.flash_messages.add(_('Unable to change state on ${title}: ${error}',
                                                      mapping={'title': ai.title, 'error': e}),
                                                    type='error')
            self.api.flash_messages.add(_('States updated'))

        state_info = _dummy_agenda_item.workflow.state_info(None, self.request)

        def _translated_state_title(state):
            for info in state_info:
                if info['name'] == state:
                    return self.api.tstring(info['title'])
            return state
        
        self.response['translated_state_title'] = _translated_state_title
        self.response['find_resource'] = find_resource
        self.response['states'] = states = ('ongoing', 'upcoming', 'closed', 'private') 
        self.response['ais'] = {}
        context_path = resource_path(self.context)
        for state in states:
            query = dict(
                path = context_path,
                content_type = 'AgendaItem',
                sort_index = 'order',
                workflow_state = state,
            )
            self.response['ais'][state] = self.api.get_metadata_for_query(**query)

        return self.response
    
    @view_config(context=IMeeting, name="order_agenda_items", renderer="templates/order_agenda_items.pt", permission=security.EDIT)
    def order_agenda_items(self):
        self.response['title'] = _(u"order_agenda_items_view_title",
                                   default = u"Drag and drop agenda items to reorder")
        post = self.request.POST
        if 'cancel' in self.request.POST:
            url = resource_url(self.context, self.request)
            return HTTPFound(location = url)

        if 'save' in post:
            controls = self.request.POST.items()
            ais = []
            order = 0
            for (k, v) in controls:
                if k == 'agenda_items':
                    ai = self.context[v]
                    ai.set_field_appstruct({'order': order})
                    order += 1
            self.api.flash_messages.add(_('Order updated'))
            
        context_path = resource_path(self.context)
        query = dict(
            path = context_path,
            content_type = 'AgendaItem',
            sort_index = 'order',
        )
        self.response['brains'] = self.api.get_metadata_for_query(**query)
        return self.response


_dummy_agenda_item = AgendaItem()
