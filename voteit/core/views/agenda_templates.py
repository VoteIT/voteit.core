from betahaus.pyracont.factories import createSchema
from deform import Form
from deform.exception import ValidationFailure
from pyramid.url import resource_url
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IAgendaTemplates
from voteit.core.models.interfaces import IAgendaTemplate
from voteit.core import security


class PermissionsView(BaseView):
    """ View for setting permissions """
    
    @view_config(context=IAgendaTemplates, renderer="templates/agenda_templates.pt", permission=security.VIEW)
    def agenda_templates(self):
        return self.response
    
    @view_config(context=IAgendaTemplate, renderer="templates/agenda_template.pt", permission=security.VIEW)
    def agenda_template(self):
        return self.response