from pyramid.view import view_config
from pyramid.url import resource_url

from deform import Form

from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IProposal
from voteit.core.security import VIEW


class AgendaItemView(BaseView):
    """ View for agenda items. """
    
    @view_config(context=IAgendaItem, renderer="templates/agenda_item.pt", permission=VIEW)
    def agenda_item_view(self):
        """ """
        #FIXME: this is just placeholders, should be filled with real data
        self.response['next_poll'] = '1 hour'
        self.response['poll_start'] = '15.00'
        self.response['poll_end'] = '16.00'
    
        self.response['discussions'] = self.context.get_content(iface=IDiscussionPost, sort_on='created')
        self.response['proposals'] = self.context.get_content(iface=IProposal)
        self.response['polls'] = self.context.get_content(iface=IPoll)
        
        ci = self.api.content_info
        url = resource_url(self.context, self.request)

        #Proposal form
        prop_schema = ci['Proposal'].schema(context=self.context, request=self.request, type='add')
        self.prop_form = Form(prop_schema, action=url+"@@add?content_type=Proposal", buttons=('add',))

        #Discussion form
        discussion_schema = ci['DiscussionPost'].schema(context=self.context, request=self.request, type='add')
        self.discussion_form = Form(discussion_schema, action=url+"@@add?content_type=DiscussionPost", buttons=('add',))
        
        #Join resources
        form_resources = self.prop_form.get_widget_resources()
        for (k, v) in self.discussion_form.get_widget_resources().items():
            if k in form_resources:
                form_resources[k].extend(v)
            else:
                form_resources[k] = v
        
        
        self.response['form_resources'] = form_resources
        self.response['proposal_form'] = self.prop_form.render()
        self.response['discussion_form'] = self.discussion_form.render()

        return self.response
