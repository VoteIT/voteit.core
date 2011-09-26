import colander
import deform
from zope.interface import implements
from pyramid.security import Allow, DENY_ALL, ALL_PERMISSIONS
from pyramid.traversal import find_interface, find_root

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.base_content import BaseContent
from voteit.core.models.unread_aware import UnreadAware
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.workflow_aware import WorkflowAware
from voteit.core.validators import html_string_validator
from voteit.core.validators import at_userid_validator

ACL = {}
ACL['published'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, security.EDIT, security.DELETE, security.RETRACT, security.MODERATE_MEETING, )),
                    (Allow, security.ROLE_MODERATOR, (security.VIEW, security.EDIT, security.DELETE, security.RETRACT, security.MODERATE_MEETING, )),
                    (Allow, security.ROLE_OWNER, (security.VIEW, security.RETRACT, )),
                    (Allow, security.ROLE_PARTICIPANT, (security.VIEW,)),
                    (Allow, security.ROLE_VIEWER, (security.VIEW,)),
                    DENY_ALL,
                ]
ACL['locked'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, security.EDIT, security.DELETE, security.MODERATE_MEETING, )),
                 (Allow, security.ROLE_MODERATOR, (security.VIEW, security.EDIT, security.DELETE, security.MODERATE_MEETING, )),
                 (Allow, security.ROLE_OWNER, security.VIEW),
                 (Allow, security.ROLE_PARTICIPANT, (security.VIEW,)),
                 (Allow, security.ROLE_VIEWER, (security.VIEW,)),
                 DENY_ALL,
                ]
ACL['closed'] = [(Allow, security.ROLE_ADMIN, security.VIEW),
                 (Allow, security.ROLE_MODERATOR, security.VIEW),
                 (Allow, security.ROLE_OWNER, security.VIEW),
                 (Allow, security.ROLE_PARTICIPANT, security.VIEW),
                 (Allow, security.ROLE_VIEWER, security.VIEW),
                 DENY_ALL,
                ]

class Proposal(BaseContent, WorkflowAware, UnreadAware):
    """ Proposal content.
        about states:
        'published' is used in ongoing meetings. This proposal is a candidate for a future poll.
        'retracted' means that the person who wrote the proposal ('Owner' role)
        doesn't stand behind it any longer and it won't be a candidate for a poll.
        'voting' is a locked state - this proposal is part of an ongoing poll.
        'denied' and 'approved' are locked states for proposals that have been part of a poll.
        They're either denied or approved.
        'unhandled' is a locked state. The agenda item closed before anything was done with this proposal.
        
        Administrators and moderators have extra privileges on proposals if the agenda item hasn't closed.
        (This is simply to help editing things to avoid mistakes.) After that, the proposals will be locked
        without any option to alter them. In that case, the ACL table 'closed' is used.
        """
    implements(IProposal, ICatalogMetadataEnabled)
    content_type = 'Proposal'
    display_name = _(u"Proposal")
    allowed_contexts = ('AgendaItem',)
    add_permission = security.ADD_PROPOSAL

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


def construct_schema(context=None, **kwargs):
    if context is None:
        KeyError("'context' is a required keyword for Proposal schemas. See construct_schema in the proposal module.")
        
    root = find_root(context)
    def _at_userid_validator(node, value):
        at_userid_validator(node, value, root.users)

    class ProposalSchema(colander.MappingSchema):
        title = colander.SchemaNode(colander.String(),
                                    title = _(u"I propose:"),
                                    validator=colander.All(html_string_validator, _at_userid_validator),
                                    widget=deform.widget.TextAreaWidget(rows=3, cols=40),)
    return ProposalSchema()


def includeme(config):
    from voteit.core.app import register_content_info
    register_content_info(construct_schema, Proposal, registry=config.registry)
