from pyramid.renderers import render

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

    def view(self, api):
        response = dict(api = api)
        return render('templates/invite_only.pt', response, request = api.request)


def includeme(config):
    config.registry.registerAdapter(InviteOnlyAP, name = InviteOnlyAP.name)
