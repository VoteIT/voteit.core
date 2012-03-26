from zope.interface import implements
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid.traversal import find_interface
from betahaus.pyracont.decorators import content_factory
from webhelpers.html.tools import auto_link
from webhelpers.html.converters import nl2br

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
        state = self.get_workflow_state()
        if state == 'published':
            return ACL['published']
        
        #Check if AI is open.
        ai = find_interface(self, IAgendaItem)
        if ai.get_workflow_state() == 'closed':
            return ACL['closed']
        
        return ACL['locked']

    def _get_title(self):
        return self.get_field_value('title', u"")
    def _set_title(self, value, key=None):
        """ Custom mutator, will transform urls to links and linebreaks to <br/> """
        value = auto_link(value)
        value = nl2br(value)
        #nl2br will also ad a \n to the end, we need to remove it so it doesn't run several times
        value = value.replace('\n', ' ')
        self.field_storage['title'] = value
    
    title = property(_get_title, _set_title)
