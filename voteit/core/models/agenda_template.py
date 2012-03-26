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


@content_factory('AgendaTemplate', title=_(u"Agenda template"))
class AgendaTemplate(BaseContent):
    """ Agenda template content type.
        See :mod:`voteit.core.models.interfaces.IAgendaTemplate`.
        All methods are documented in the interface of this class.
    """
    implements(IAgendaTemplate)
    content_type = 'AgendaTemplate'
    display_name = _(u"Agenda template")
    allowed_contexts = ('AgendaTemplates')
    add_permission = security.ADD_AGENDA_TEMPLATE
    schemas = {'add': 'AgendaTemplateSchema', 'edit': 'AgendaTemplateSchema'}

    __acl__ = [(Allow, security.ROLE_ADMIN, (security.EDIT, security.VIEW, security.DELETE, security.MANAGE_SERVER, )),
               (Allow, security.ROLE_OWNER, (security.EDIT, security.VIEW, security.DELETE,)),
               DENY_ALL,
              ]
    
    def populate_meeting(self, meeting):
        for item in self.get_field_value('agenda_items', ()):
            obj = createContent('AgendaItem', **item)
            slug = generate_slug(meeting, obj.title)
            meeting[slug] = obj
