from __future__ import unicode_literals

from voteit.core.models.access_policy import AccessPolicy
from voteit.core import VoteITMF as _


class InviteOnlyAP(AccessPolicy):
    """ Only allow invitation emails as access method for users. """
    name = 'invite_only'
    title =  _("meeting_access_invite_only_label",
               default = "Access will only be granted through invites (Default)")
    description = _("invite_only_meeting_access_request_description",
                    default = """This meeting is invite only.
                    That means that a mail will be sent with an access ticket.
                    Contact meeting moderators for more information.""")
    def schema(self):
        pass


def includeme(config):
    config.registry.registerAdapter(InviteOnlyAP, name = InviteOnlyAP.name)
