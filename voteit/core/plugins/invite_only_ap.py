from pyramid.httpexceptions import HTTPFound

from voteit.core.models.access_policy import AccessPolicy
from voteit.core import VoteITMF as _


class InviteOnlyAP(AccessPolicy):
    """ Only allow invitation emails as access method for users. """
    name = 'invite_only'
    title =  _(u"meeting_access_invite_only_label",
               default = u"Access will only be granted through invites (Default)")
    description = _(u"invite_only_meeting_access_request_description",
                    default = u"""This meeting is invite only.
                    That means that a mail will be sent with an access ticket.
                    Contact meeting moderators for more information.""")
    view = True

    def render_view(self, api):
        msg = _(u"invite_only_ap_msg",
                default = u"This meeting you tried to access is invite-only. "
                    u"Normally the moderators will send a mail with an access ticket. "
                    u"Contact meeting moderators for more information.")
        api.flash_messages.add(msg)
        return HTTPFound(location = api.request.application_url)


def includeme(config):
    config.registry.registerAdapter(InviteOnlyAP, name = InviteOnlyAP.name)
