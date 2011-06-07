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
CHANGE_PASSWORD = 'Change Password'
MANAGE_GROUPS = 'Manage Groups'
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

def groupfinder(name, request):
    """ Get groups for the current user. See models/security_aware.py
    """
    return request.context.get_groups(name)
