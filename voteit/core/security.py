from zope.component import getUtility
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.traversal import find_root
from pyramid.security import Authenticated
from pyramid.security import Everyone
from zope.component.event import objectEventNotify

from voteit.core.events import WorkflowStateChange
from voteit.core import VoteITMF as _


#Roles, which are the same as groups really
ROLE_ADMIN = 'role:Admin'
ROLE_MODERATOR = 'role:Moderator'
ROLE_PARTICIPANT = 'role:Participant'
ROLE_VOTER = 'role:Voter'
ROLE_VIEWER = 'role:Viewer'
ROLE_OWNER = 'role:Owner'


#Global Permissions
VIEW = 'View'
EDIT = 'Edit'
DELETE = 'Delete'
REGISTER = 'Register'
RETRACT = 'Retract'
CHANGE_WORKFLOW_STATE = 'Change Workflow State'
CHANGE_PASSWORD = 'Change Password'
MANAGE_GROUPS = 'Manage Groups'
MANAGE_SERVER = 'Manage Server'
MODERATE_MEETING = 'Moderate Meeting'
REQUEST_MEETING_ACCESS = 'Request Meeting Access'

#FIXME: We need to separate Edit and workflow permissions for most content types

#Add permissions
#Note: For add permissions, check each content types class
ADD_AGENDA_ITEM = 'Add Agenda Item'
ADD_DISCUSSION_POST = 'Add Discussion Post'
ADD_MEETING = 'Add Meeting'
ADD_POLL = 'Add Poll'
ADD_PROPOSAL = 'Add Proposal'
ADD_USER = 'Add User'
ADD_VOTE = 'Add Vote'

#All add permissions except vote!
REGULAR_ADD_PERMISSIONS = (ADD_AGENDA_ITEM,
                           ADD_DISCUSSION_POST,
                           ADD_MEETING,
                           ADD_POLL,
                           ADD_PROPOSAL,
                           ADD_USER,)

ROOT_ROLES = ((ROLE_ADMIN, _(u'Administrator')),)
MEETING_ROLES = ((ROLE_MODERATOR, _(u'Moderator')),
                 (ROLE_PARTICIPANT, _(u'Participant')),
                 (ROLE_VOTER, _(u'Voter')),
                 (ROLE_VIEWER, _(u'View only')),
                )


# An empty value tells the catalog to match anything, whereas when
# there are no principals with permission to view we want for there
# to be no matches. This string is in other words forbidden to use
# as a userid, group or role name.
NEVER_EVER_PRINCIPAL = 'NO ONE no way NO HOW'

def groupfinder(name, request):
    """ Get groups for the current user. See models/security_aware.py
        This is also a callback for the Authorization policy.
    """
    return request.context.get_groups(name)

#Authentication policies
authn_policy = AuthTktAuthenticationPolicy(secret='sosecret',
                                           callback=groupfinder)
authz_policy = ACLAuthorizationPolicy()


def find_authorized_userids(context, permissions):
    """ Return a set of all userids that fullfill all of the permissions in permissions.

        Special permission check that is agnostic of the request.context attribute.
        (As opposed to pyramid.security.has_permission)
        Don't use anything else than this one to determine permissions for something
        where the request.context isn't the same as context, for instance another 
        object that appears in a listing.
        
        Warning: This method will of course consume CPU. Use it where appropriate.
    """
    authz_policy = getUtility(IAuthorizationPolicy)
    root = find_root(context)
    allowed_userids = set()
    
    for userid in root.users.keys():
        principals = context_effective_principals(context, userid)
        res = [authz_policy.permits(context, principals, perm) for perm in permissions]
        if len(res) == sum(res): #Bool true counts as 1, and false as 0
            allowed_userids.add(userid)
    return allowed_userids

def context_effective_principals(context, userid):
    """ Special version of pyramid.security.effective_principals that
        adds groups based on context instead of request.context
        
        A note about Authenticated: It doesn't mean that the current user is authenticated,
        rather than someone with a userid are part of the Authenticated group, since by using
        a userid they will have logged in :)
    """
    effective_principals = [Everyone]
    if userid is None:
        return effective_principals
    
    groups = context.get_groups(userid)
    
    effective_principals.append(Authenticated)
    effective_principals.append(userid)
    effective_principals.extend(groups)
    return effective_principals    

def unrestricted_wf_transition_to(obj, state):
    """ Transition to a stade WITHOUT checking permission.
    """
    old_state = obj.get_workflow_state()
    obj.workflow._transition_to_state(obj, state, guards=())
    objectEventNotify(WorkflowStateChange(obj, old_state, state))
