from arche.views.base import BaseView
from pyramid.httpexceptions import HTTPFound
from pyramid.traversal import find_resource
from pyramid.traversal import resource_path
from pyramid.view import view_config
from repoze.workflow.workflow import WorkflowError

from voteit.core import _
from voteit.core import security
from voteit.core.models.agenda_item import AgendaItem
from voteit.core.models.interfaces import IMeeting


@view_config(context = IMeeting, name = "manage_agenda", renderer = "voteit.core:templates/manage_agenda.pt", permission = security.EDIT)
class ManageAgendaItemsView(BaseView):

    def __call__(self):
        post = self.request.POST
        if 'cancel' in self.request.POST:
            url = self.request.resource_url(self.context)
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
                        self.flash_messages.add(_('Unable to change state on ${title}: ${error}',
                                                      mapping={'title': ai.title, 'error': e}),
                                                    type='error')
            self.flash_messages.add(_('States updated'))

        state_info = _dummy_agenda_item.workflow.state_info(None, self.request)
        tstring = _
        def _translated_state_title(state):
            for info in state_info:
                if info['name'] == state:
                    return tstring(info['title'])
            return state
        response = {}
        
        response['translated_state_title'] = _translated_state_title
        response['find_resource'] = find_resource
        response['states'] = states = ('ongoing', 'upcoming', 'closed', 'private') 
        response['ais'] = {}
        context_path = resource_path(self.context)
        for state in states:
            query = dict(
                path = context_path,
                type_name = 'AgendaItem',
                sort_index = 'order',
                workflow_state = state,
                resolve = True,
            )
            response['ais'][state] = self.catalog_search(**query)
        return response

#FIXME: :P
_dummy_agenda_item = AgendaItem()
