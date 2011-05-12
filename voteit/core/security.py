
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
REGISTER = 'Register'
CHANGE_PASSWORD = 'Change Password'
MANAGE_GROUPS = 'Manage Groups'

#Add permissions
#Note: For add permissions, check each content types class
ADD_AGENDA_ITEM = 'Add Agenda Item'
ADD_MEETING = 'Add Meeting'
ADD_POLL = 'Add Poll'
ADD_PROPOSAL = 'Add Proposal'
ADD_USER = 'Add User'
ADD_VOTE = 'Add Vote'

ALL_ADD_PERMISSIONS = (ADD_AGENDA_ITEM,
                       ADD_MEETING,
                       ADD_POLL,
                       ADD_PROPOSAL,
                       ADD_USER,
                       ADD_VOTE,)

def groupfinder(name, request):
    """ Get groups for the current user. See models/security_aware.py
    """
    return request.context.get_groups(name)
    
def workflowpermission(permission, context, request):
    from pyramid.security import authenticated_userid
    userid = authenticated_userid(request)
    groups = context.get_groups(userid)
    print groups
    if permission in groups or ROLE_MODERATOR in groups or ROLE_ADMIN in groups:
        return True
    else:
        return False
