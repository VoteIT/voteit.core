from pyramid.events import subscriber
from pyramid.security import authenticated_userid
from pyramid.threadlocal import get_current_request
from repoze.folder.interfaces import IObjectAddedEvent

from voteit.core.models.interfaces import IMeeting
from voteit.core.security import ROLE_MODERATOR


@subscriber([IMeeting, IObjectAddedEvent])
def make_current_user_moderator(obj, event):
    request = get_current_request()
    userid = authenticated_userid(request)
    obj.add_groups(userid, (ROLE_MODERATOR,))
