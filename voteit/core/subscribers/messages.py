""" Automatic messaging on some events. """
from pyramid.events import subscriber
from pyramid.traversal import find_interface
from repoze.folder.interfaces import IObjectAddedEvent
from zope.component import getUtility

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import ISQLSession
from voteit.core.models.message import Messages
from voteit.core.security import VIEW
from voteit.core.security import find_authorized_userids


@subscriber(IAgendaItem, IObjectAddedEvent)
@subscriber(IProposal, IObjectAddedEvent)
@subscriber(IPoll, IObjectAddedEvent)
def message_content_added(obj, event):
    meeting = find_interface(obj, IMeeting)

    userids = find_authorized_userids(obj, (VIEW,))

    session = getUtility(ISQLSession)()
    messages = Messages(session)
    for userid in userids:
        messages.add(
            meeting.uid,
            u"New %s added" % obj.display_name,
            tags=('added',),
            contextuid=obj.uid,
            userid=userid,
        )
