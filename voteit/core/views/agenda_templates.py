from betahaus.pyracont.factories import createSchema
from betahaus.pyracont.factories import createContent
from deform import Form
from deform.exception import ValidationFailure
from pyramid.url import resource_url
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.traversal import find_root

from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IAgendaTemplates
from voteit.core.models.interfaces import IAgendaTemplate
from voteit.core.models.interfaces import IMeeting
from voteit.core import security


class AgendaTempalteView(BaseView):
    """ View for Agenda tempaltes """
    
    @view_config(context=IAgendaTemplates, renderer="templates/agenda_templates.pt", permission=security.VIEW)
    def agenda_templates(self):
        self.response['agenda_templates'] = self.context
        
        return self.response
    
    @view_config(context=IAgendaTemplate, renderer="templates/agenda_template.pt", permission=security.VIEW)
    def agenda_template(self):
        return self.response
    
    @view_config(context=IMeeting, name="agenda_templates", renderer="templates/agenda_templates.pt", permission=security.EDIT)
    def agenda_template_select(self):
        #FIXME: Should this be a migrate script?
        try:
            agenda_templates = self.api.root['agenda_templates']
        except KeyError:
            obj = createContent('AgendaTemplates', title = _(u"Agenda templates"), creators = ['admin'])
            agenda_templates = self.api.root['agenda_templates'] = obj
        
        get = self.request.GET
        if 'apply' in get:
            template_name = get['apply']
            if template_name in agenda_templates:
                template = agenda_templates[template_name]
                template.populate_meeting(self.context)
                
                msg = _(u"agenda_template_apply_template_success",
                        default = u"Selected template applied to meeting.")
                self.api.flash_messages.add(msg)
                
                return HTTPFound(location = resource_url(self.context, self.request))
            else:
                err_msg = _(u"agenda_template_apply_invalid_template",
                        default = u"No template named ${template} could be found.",
                        mapping = {'template': template_name})
                self.api.flash_messages.add(err_msg, type="error")
        
        self.response['agenda_templates'] = agenda_templates
        
        return self.response