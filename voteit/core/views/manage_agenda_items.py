from arche.views.base import BaseView
from pyramid.httpexceptions import HTTPFound
from pyramid.traversal import find_resource
from pyramid.view import view_config
from repoze.workflow.workflow import WorkflowError

from voteit.core import _
from voteit.core import security
from voteit.core.models.agenda_item import AgendaItem
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting


_BLOCK_VALS = {
    'default': False,
    'blocked': True,
}

@view_config(context = IMeeting,
             name = "manage_agenda",
             renderer = "voteit.core:templates/manage_agenda.pt",
             permission = security.EDIT)
class ManageAgendaItemsView(BaseView):

    def __call__(self):
        post = self.request.POST
        if 'cancel' in self.request.POST:
            url = self.request.resource_url(self.context)
            return HTTPFound(location = url)
        if 'change' in post:
            state_id = self.request.POST['state_id']
            block_proposals = self.request.POST.get('block_proposals', None)
            block_proposals = _BLOCK_VALS.get(block_proposals, None)
            block_discussion = self.request.POST.get('block_discussion', None)
            block_discussion = _BLOCK_VALS.get(block_discussion, None)

            controls = self.request.POST.items()
            agenda_items = []
            for (k, v) in controls:
                if k == 'ais':
                    agenda_items.append(self.context[v])
            output_msg = ""
            translate = self.request.localizer.translate
            #WF state change
            if state_id:
                states_changed = 0
                for ai in agenda_items:
                    try:
                        ai.set_workflow_state(self.request, state_id)
                        states_changed += 1
                    except WorkflowError, e:
                        self.flash_messages.add(_('Unable to change state on ${title}: ${error}',
                                                      mapping={'title': ai.title, 'error': e}),
                                                    type='danger')
                if states_changed:
                    output_msg += translate(_("${num} changed state", mapping={'num': states_changed}))
                    output_msg += "<br/>"
            #Block states
            if block_proposals != None or block_discussion != None:
                blocked = 0
                for ai in agenda_items:
                    blocked += 1
                    if block_proposals != None:
                        ai.set_field_value('proposal_block', block_proposals)
                    if block_discussion != None:
                        ai.set_field_value('discussion_block', block_discussion)
                if blocked:
                    output_msg += translate(
                        _("Changing block state for ${num} agenda items.",
                          mapping = {'num': blocked})
                    )

            if output_msg:
                self.flash_messages.add(output_msg, type='success')
            else:
                self.flash_messages.add(_('Nothing updated'), type='warning')
            return HTTPFound(location=self.request.resource_url(self.context, 'manage_agenda'))

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
        response['ais'] = ais = {}
        for state in states:
            ais[state] = []
        for obj in self.context.values():
            if IAgendaItem.providedBy(obj):
                ais[obj.get_workflow_state()].append(obj)
        return response

#FIXME: :P
_dummy_agenda_item = AgendaItem()
