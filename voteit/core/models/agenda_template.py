from zope.interface import implements
from pyramid.security import Allow
from pyramid.security import DENY_ALL

from betahaus.pyracont.decorators import content_factory
from betahaus.pyracont.factories import createContent

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.helpers import generate_slug
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IAgendaTemplate
from voteit.core.models.agenda_item import AgendaItem



@content_factory('AgendaTemplate', title=_(u"Agenda template"))
class AgendaTemplate(BaseContent):
    """ Agenda Template content """
    implements(IAgendaTemplate)
    content_type = 'AgendaTemplate'
    display_name = _(u"Agenda template")
    allowed_contexts = ('AgendaTemplates')
    #FIXME: maybe this should have its own add permission 
    add_permission = security.ADD_MEETING
    schemas = {'add': 'AgendaTemplateSchema', 'edit': 'AgendaTemplateSchema'}

    #FIXME: maybe this should have its own use permission
    __acl__ = [(Allow, security.ROLE_ADMIN, (security.EDIT, security.VIEW, security.DELETE,)),
               (Allow, security.ROLE_OWNER, (security.EDIT, security.VIEW, security.DELETE,)),
               (Allow, security.ROLE_VIEWER, (security.VIEW,)),
               DENY_ALL,
              ]
    
    def populate_meeting(self, meeting):
        for item in self.get_field_value('agenda_items', ()):
            obj = AgendaItem(**item)
            slug = generate_slug(meeting, obj.title)
            meeting[slug] = obj