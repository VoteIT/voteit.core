from __future__ import unicode_literals
from UserDict import IterableUserDict
from calendar import timegm

from BTrees.OOBTree import OOBTree
from arche.interfaces import IObjectUpdatedEvent
from arche.utils import utcnow
from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from repoze.folder.interfaces import IObjectAddedEvent
from zope.interface import implementer

from voteit.core import _
from voteit.core import log
from voteit.core.helpers import get_at_userids
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IMentioned
from voteit.core.models.interfaces import IProposal


@implementer(IMentioned)
class Mentioned(IterableUserDict):
    """ Handles mentioned userids in a context.
        Use add function to add a userid with a unix timestamp as value.
    """

    def __init__(self, context):
        self.context = context
        self.data = getattr(context, '__mentioned__', {})

    def __setitem__(self, key, item):
        if not isinstance(self.data, OOBTree):
            self.data = self.context.__mentioned__ = OOBTree()
        self.data[key] = item

    def add(self, userid):
        self[userid] = timegm(utcnow().timetuple())


def email_users_about_mention(obj, event):
    """ Sends email to users when they are mentioned in posts and proposals,
        if mention_notification_setting is set to True.
    """
    meeting = find_interface(obj, IMeeting)
    if not meeting: #pragma : no cover
        log.warn("No meeting found, aborting notification")
        return
    if not meeting.mention_notification_setting:
        return
    mentioned = IMentioned(obj)
    users = find_root(meeting).users
    request = get_current_request()
    for userid in get_at_userids(obj.text):
        if userid in mentioned:
            continue
        if userid in users:
            user = users[userid]
            if send_mention_notification(obj, request, user):
                mentioned.add(userid)
        else:
            log.debug("Notification failed, %r not found in users folder.", userid)

def send_mention_notification(context, request, user):
    """ Sends an email when the user is mentioned in a proposal or a discussion post.

        context should be something that's adaptable by IMentioned. (Like DiscussionPost or Proposal)

        Returns userid at success
    """
    email = user.email
    if email:
        meeting = find_interface(context, IMeeting)
        agenda_item = find_interface(context, IAgendaItem)
        #FIXME: Email should use a proper template
        url = request.resource_url(context)
        link = "<a href=\"%s\">%s</a>" % (url, url)
        body = request.localizer.translate(_('mentioned_notification',
                                             default = "You have been mentioned in ${meeting} on ${agenda_item}. "
                                             "Click the following link to go there, ${link}.",
                                             mapping = {'meeting':meeting.title,
                                                        'agenda_item': agenda_item.title,
                                                        'link': link,},))
        subject = _("Mentioned in ${meeting_title}",
                    mapping = {'meeting_title': meeting.title})
        request.send_email(subject, email, body)
        return user.userid

def includeme(config):
    config.registry.registerAdapter(Mentioned, required = [IProposal])
    config.registry.registerAdapter(Mentioned, required = [IDiscussionPost])
    config.add_subscriber(email_users_about_mention, [IProposal, IObjectAddedEvent])
    config.add_subscriber(email_users_about_mention, [IProposal, IObjectUpdatedEvent])
    config.add_subscriber(email_users_about_mention, [IDiscussionPost, IObjectAddedEvent])
    config.add_subscriber(email_users_about_mention, [IDiscussionPost, IObjectUpdatedEvent])
