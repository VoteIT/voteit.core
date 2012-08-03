from zope.interface import implements
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid.traversal import find_interface
from betahaus.pyracont.decorators import content_factory

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.workflow_aware import WorkflowAware


_PUBLISHED_MODERATOR_PERMS = (security.VIEW,
                              security.EDIT,
                              security.DELETE,
                              security.RETRACT,
                              security.MODERATE_MEETING,)
_LOCKED_MODERATOR_PERMS = (security.VIEW,
                           security.EDIT,
                           security.DELETE,
                           security.MODERATE_MEETING, )

ACL = {}
ACL['published'] = [(Allow, security.ROLE_ADMIN, _PUBLISHED_MODERATOR_PERMS),
                    (Allow, security.ROLE_MODERATOR, _PUBLISHED_MODERATOR_PERMS),
                    (Allow, security.ROLE_OWNER, (security.RETRACT, )),
                    (Allow, security.ROLE_PROPOSE, (security.VIEW,)),
                    (Allow, security.ROLE_DISCUSS, (security.VIEW,)),
                    (Allow, security.ROLE_VOTER, (security.VIEW,)),
                    (Allow, security.ROLE_VIEWER, (security.VIEW,)),
                    DENY_ALL,
                ]
ACL['locked'] = [(Allow, security.ROLE_ADMIN, _LOCKED_MODERATOR_PERMS),
                 (Allow, security.ROLE_MODERATOR, _LOCKED_MODERATOR_PERMS),
                 (Allow, security.ROLE_PROPOSE, (security.VIEW,)),
                 (Allow, security.ROLE_DISCUSS, (security.VIEW,)),
                 (Allow, security.ROLE_VOTER, (security.VIEW,)),
                 (Allow, security.ROLE_VIEWER, (security.VIEW,)),
                 DENY_ALL,
                ]
ACL['closed'] = [(Allow, security.ROLE_ADMIN, security.VIEW),
                 (Allow, security.ROLE_MODERATOR, security.VIEW),
                 (Allow, security.ROLE_PROPOSE, (security.VIEW,)),
                 (Allow, security.ROLE_DISCUSS, (security.VIEW,)),
                 (Allow, security.ROLE_VOTER, (security.VIEW,)),
                 (Allow, security.ROLE_VIEWER, security.VIEW),
                 DENY_ALL,
                ]
ACL['private'] = [(Allow, security.ROLE_ADMIN, _PUBLISHED_MODERATOR_PERMS),
                  (Allow, security.ROLE_MODERATOR, _PUBLISHED_MODERATOR_PERMS),
                  DENY_ALL,
                  ]


@content_factory('Proposal', title=_(u"Proposal"))
class Proposal(BaseContent, WorkflowAware):
    """ Proposal content type.
        See :mod:`voteit.core.models.interfaces.IProposal`.
        All methods are documented in the interface of this class.
    """

    implements(IProposal, ICatalogMetadataEnabled)
    content_type = 'Proposal'
    display_name = _(u"Proposal")
    allowed_contexts = ('AgendaItem',)
    add_permission = security.ADD_PROPOSAL
    schemas = {'add': 'ProposalSchema',
               'edit': 'ProposalSchema'}
    custom_mutators = {'title': '_set_title'}

    @property
    def __acl__(self):
        ai = find_interface(self, IAgendaItem)
        ai_state = ai.get_workflow_state()
        #If ai is private, use private
        if ai_state == 'private':
            return ACL['private']
        state = self.get_workflow_state()
        if state == 'published':
            return ACL['published']
        #Check if AI is open.
        if ai_state == 'closed':
            return ACL['closed']
        return ACL['locked']

    def _get_title(self):
        return self.get_field_value('title', u"")
    
    def _set_title(self, value, key=None):
        self.field_storage['title'] = value
    
    title = property(_get_title, _set_title)
