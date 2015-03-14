from arche.security import get_acl_registry
from pyramid.traversal import find_interface
from zope.interface import implementer

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.helpers import strip_and_truncate
from voteit.core.helpers import tags_from_text
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.workflow_aware import WorkflowAware


@implementer(IProposal, ICatalogMetadataEnabled)
class Proposal(BaseContent, WorkflowAware):
    """ Proposal content type.
        See :mod:`voteit.core.models.interfaces.IProposal`.
        All methods are documented in the interface of this class.
    """
    type_name = 'Proposal'
    type_title = _(u"Proposal")
    add_permission = security.ADD_PROPOSAL
    #custom_mutators = {'title': '_set_title'}

    @property
    def __acl__(self):
        ai = find_interface(self, IAgendaItem)
        ai_state = ai.get_workflow_state()
        acl = get_acl_registry()
        #If ai is private, use private
        if ai_state == 'private':
            return acl.get_acl('Proposal:private')
        if ai_state == 'closed':
            return acl.get_acl('Proposal:closed')
        state = self.get_workflow_state()
        acl_name = "Proposal:%s" % state
        if acl_name in acl:
            return acl.get_acl(acl_name)
        return acl.get_acl('Proposal:locked')

    @property
    def title(self):
        return strip_and_truncate(self.text, limit = 100, symbol = '')
    @title.setter
    def title(self, value):
        raise NotImplementedError("Tried to set title on Proposal")

    @property
    def text(self):
        return self.get_field_value('text', '')
    @text.setter
    def text(self, value):
        self.set_field_value('text', value)

#     def _get_title(self):
#         return self.get_field_value('title', u"")
# 
#     def _set_title(self, value, key=None):
#         self.field_storage['title'] = value
# 
#     title = property(_get_title, _set_title)

    @property
    def tags(self): #arche compat
        tags = tags_from_text(self.text)
        aid = self.get_field_value('aid', None)
        if aid is not None and aid not in tags:
            tags.append(aid)
        return tags
    @tags.setter
    def tags(self, value):
        print "Tags shouldn't be set like this"

    @property
    def aid(self): #arche compat
        return self.get_field_value('aid', '')
    @aid.setter
    def aid(self, value):
        self.set_field_value('aid', value)

    @property #arche compat
    def aid_int(self):
        return self.get_field_value('aid_int', None)
    @aid_int.setter
    def aid_int(self, value):
        self.set_field_value('aid_int', value)


def includeme(config):
    config.add_content_factory(Proposal, addable_to = 'AgendaItem')
    _PUBLISHED_MODERATOR_PERMS = (security.VIEW,
                                  security.EDIT,
                                  security.DELETE,
                                  security.RETRACT,
                                  security.MODERATE_MEETING,)
    _LOCKED_MODERATOR_PERMS = (security.VIEW,
                               security.EDIT,
                               security.DELETE,
                               security.MODERATE_MEETING, )
    aclreg = config.registry.acl
    published = aclreg.new_acl('Proposal:published')
    published.add(security.ROLE_ADMIN, _PUBLISHED_MODERATOR_PERMS)
    published.add(security.ROLE_MODERATOR, _PUBLISHED_MODERATOR_PERMS)
    published.add(security.ROLE_OWNER, security.RETRACT)
    published.add(security.ROLE_VIEWER, security.VIEW)
    locked = aclreg.new_acl('Proposal:locked')
    locked.add(security.ROLE_ADMIN, _LOCKED_MODERATOR_PERMS)
    locked.add(security.ROLE_MODERATOR, _LOCKED_MODERATOR_PERMS)
    locked.add(security.ROLE_VIEWER, security.VIEW)
    closed = aclreg.new_acl('Proposal:closed')
    closed.add(security.ROLE_ADMIN, security.VIEW)
    closed.add(security.ROLE_MODERATOR, security.VIEW)
    closed.add(security.ROLE_VIEWER, security.VIEW)
    private = aclreg.new_acl('Proposal:private', description ="When Agenda Item is private")
    private.add(security.ROLE_ADMIN, _PUBLISHED_MODERATOR_PERMS)
    private.add(security.ROLE_MODERATOR, _PUBLISHED_MODERATOR_PERMS)
