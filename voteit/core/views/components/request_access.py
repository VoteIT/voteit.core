import colander
from deform import Form
from deform.exception import ValidationFailure
from betahaus.viewcomponent import view_action
from pyramid.url import resource_url
from pyramid.httpexceptions import HTTPFound

from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_request
from voteit.core.models.schemas import button_cancel
from voteit.core import VoteITMF as _
from voteit.core.security import ROLE_VIEWER
from voteit.core.models.interfaces import IMeeting


PUBLIC_TITLE = _(u"meeting_access_public_label",
                 default = u"All authenticated members will be given view permission INSTANTLY if they request it.")
@view_action('request_meeting_access', 'public', title = PUBLIC_TITLE, interface = IMeeting)
def public_request_meeting_access(context, request, va, **kw):
    if context.get_field_value('access_policy') != 'public':
        raise Exception("ViewAction for request meeting access public was called, but that access policy wasn't set for this meeting.")
    api = kw['api']
    if not api.userid:
        raise  Exception("Can't find userid")
    schema = colander.Schema()
    add_csrf_token(context, request, schema)
    form = Form(schema, buttons=(button_request, button_cancel,))
    response = {'api': api}
    post = request.POST
    if 'request' in post:
        controls = post.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure, e:
            response['form'] = e.render()
            return response
        context.add_groups(api.userid, [ROLE_VIEWER], event = True)
        api.flash_messages.add(_(u"Access granted!"))
        url = resource_url(context, request)
        return HTTPFound(location=url)

    msg = _(u"public_meeting_access_request_description",
            default = u"This meeting allows anyone to request access to it. You only need to click below to be allowed to view the meeting.")
    api.flash_messages.add(msg)
    #No action - Render form
    return form.render()


INVITE_ONLY_TITLE = _(u"meeting_access_invite_only_label",
                      default = u"Access will only be granted through invites (Default)")
@view_action('request_meeting_access', 'invite_only', title = INVITE_ONLY_TITLE, interface = IMeeting)
def invite_only_request_meeting_access(context, request, va, **kw):
    """ Default action, simply block access. """
    api = kw['api']
    msg = _(u"invite_only_meeting_access_request_description",
            default = u"This meeting is invite only. That means that a mail will be sent with an access ticket. Contact meeting moderators for more information.")
    api.flash_messages.add(msg)
    url = resource_url(api.root, request)
    return HTTPFound(location=url)
