import re

from repoze.folder.interfaces import IObjectAddedEvent
from pyramid.events import subscriber
from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_root
from pyramid.traversal import find_interface

from voteit.core.events import ObjectUpdatedEvent
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IMeeting
from voteit.core.helpers import AT_PATTERN


@subscriber([IProposal, IObjectAddedEvent])
@subscriber([IProposal, ObjectUpdatedEvent])
@subscriber([IDiscussionPost, IObjectAddedEvent])
@subscriber([IDiscussionPost, ObjectUpdatedEvent])
def notify(obj, event):
    """ Sends email to users when they are mentioned in posts and proposals,
        if mention_notification_setting is set to True.
    """
    meeting = find_interface(obj, IMeeting)
    assert meeting
    if not meeting.get_field_value('mention_notification_setting', True):
        return
    users = find_root(obj).users
    request = get_current_request()
    for matchobj in re.finditer(AT_PATTERN, obj.title):
        # The pattern contains a space so we only find usernames that
        # has a whitespace in front
        space, userid = matchobj.group(1, 2)
        #Force lowercase userid
        userid = userid.lower()
        # check so the user is not already mentioned
        if userid not in obj.mentioned: 
            user = users[userid]
            user.send_mention_notification(obj, request)
            # add user to mentioned
            obj.add_mention(userid)
