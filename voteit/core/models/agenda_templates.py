from zope.interface import implementer
from pyramid.security import Allow
from pyramid.security import DENY_ALL

from voteit.core import VoteITMF as _
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IAgendaTemplates
from voteit.core import security
from betahaus.pyracont.decorators import content_factory


#@content_factory('AgendaTemplates', title=_(u"Agenda templates"))
@implementer(IAgendaTemplates)
class AgendaTemplates(BaseContent):
    """ Agenda templates content type.
        See :mod:`voteit.core.models.interfaces.IAgendaTemplates`.
        All methods are documented in the interface of this class.
    """
    type_name = 'AgendaTemplates'
    type_title = _(u"Agenda templates")
    #allowed_contexts = ()

    __acl__ = [(Allow, security.ROLE_ADMIN, (security.EDIT, security.VIEW,
                                             security.MANAGE_SERVER, security.ADD_AGENDA_TEMPLATE, )),
               DENY_ALL]


def includeme(config):
    config.add_content_factory(AgendaTemplates)
