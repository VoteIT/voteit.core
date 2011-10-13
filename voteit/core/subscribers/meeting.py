from pyramid.events import subscriber
from pyramid.security import authenticated_userid
from pyramid.threadlocal import get_current_request
from repoze.folder.interfaces import IObjectAddedEvent

from voteit.core.models.interfaces import IMeeting
from voteit.core.security import ROLE_MODERATOR
from voteit.core.security import ROLE_VOTER


@subscriber([IMeeting, IObjectAddedEvent])
def make_current_user_moderator(obj, event):
    """ When a new meeting is added, make the user who added it
        moderator and voter.
    """
    request = get_current_request()
    userid = authenticated_userid(request)
    if userid:
        obj.add_groups(userid, (ROLE_MODERATOR, ROLE_VOTER))
