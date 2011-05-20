from pyramid.view import view_config
from pyramid.url import resource_url

from deform import Form

from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.views.api import APIView
from voteit.core.security import VIEW

class AgendaItemView(BaseView):
    """ View for agenda items. """
    
    @view_config(context=IAgendaItem, renderer="templates/agenda_item.pt", permission=VIEW)
    def agenda_item_view(self):
        """ """
        #FIXME: this is just placeholders, should be filled with real data
        self.response['number_of_proposals'] = 2
        self.response['number_of_posts'] = '10'
        self.response['number_of_participants'] = 4
        self.response['next_poll'] = '1 hour'
        self.response['poll_start'] = '15.00'
        self.response['poll_end'] = '16.00'
        
        #Add proposal form
        ftis = self.api.content_info
        schema = ftis['Proposal'].schema(context=self.context, request=self.request, type='add')
        url = resource_url(self.context, self.request)
        self.form = Form(schema, action=url+"@@add?content_type=Proposal", buttons=('add',))
        self.response['form_resources'] = self.form.get_widget_resources()
        self.response['proposal_form'] = self.form.render()
        
        return self.response
