from BTrees.OOBTree import OOBTree
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
from voteit.core.models.date_time_util import utcnow
from voteit.core.models.workflow_aware import WorkflowAware
from voteit.core.models.tags import Tags


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
class Proposal(BaseContent, WorkflowAware, Tags):
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
               'edit': 'ProposalSchema',
               'mentioned': '_set_mentioned'}
    custom_mutators = {'title': '_set_title',
                       'aid': '_set_aid',
                       'mentioned': '_get_mentioned'}

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
        # add tags in title to tags
        self._find_tags(value)
    
    title = property(_get_title, _set_title)
    
    def _set_aid(self, value, key=None):
        self.field_storage['aid'] = value
        # add aid to tags
        self.add_tag(value)
        
    def _get_mentioned(self, key = None, default = OOBTree()):
        mentioned = getattr(self, '__mentioned__', None)
        if mentioned is None:
            mentioned = self.__mentioned__ =  OOBTree()
        return mentioned

    def _set_mentioned(self, value, key = None):
        self._get_mentioned()['mentioned'] = value

    mentioned = property(_get_mentioned, _set_mentioned)
    
    def add_mention(self, userid):
        self.mentioned[userid] = utcnow()