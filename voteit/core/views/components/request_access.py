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
from voteit.core.security import ROLE_DISCUSS
from voteit.core.security import ROLE_PROPOSE
from voteit.core.security import ROLE_VOTER
from voteit.core.models.interfaces import IMeeting

#FIXME: We repeat a lot of code here that could be refactored.


@view_action('request_meeting_access', 'public',
             interface = IMeeting,
             title = _(u"meeting_access_public_label",
                       default = u"All users will be given view permission INSTANTLY if they request it."),)
def public_request_meeting_access(context, request, va, **kw):
    if context.get_field_value('access_policy') != 'public':
        raise Exception("ViewAction for request meeting access public was called, but that access policy wasn't set for this meeting.")
    api = kw['api']
    if not api.userid:
        raise Exception("Can't find userid")
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


@view_action('request_meeting_access', 'all_participant_permissions',
             interface = IMeeting,
             title = _(u"meeting_access_all_participant_permissions_label",
                       default = u"All users will be given view, propose, discuss and vote permissions INSTANTLY if they request it."),)
def all_participant_permissions_meeting_access(context, request, va, **kw):
    if context.get_field_value('access_policy') != 'all_participant_permissions':
        raise Exception("ViewAction for request meeting access all_participant_permissions was called, but that access policy wasn't set for this meeting.")
    api = kw['api']
    if not api.userid:
        raise Exception("Can't find userid")
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
        context.add_groups(api.userid, [ROLE_PROPOSE, ROLE_DISCUSS, ROLE_VOTER], event = True)
        api.flash_messages.add(_(u"Access granted!"))
        url = resource_url(context, request)
        return HTTPFound(location=url)

    msg = _(u"all_participant_permissions_meeting_access_request_description",
            default = u"This meeting allows anyone to request access to it. You only need to click below to get all participant permissions instantly.")
    api.flash_messages.add(msg)
    #No action - Render form
    return form.render()


@view_action('request_meeting_access', 'invite_only', interface = IMeeting,
             title = _(u"meeting_access_invite_only_label",
                      default = u"Access will only be granted through invites (Default)"))
def invite_only_request_meeting_access(context, request, va, **kw):
    """ Default action, simply block access. """
    api = kw['api']
    msg = _(u"invite_only_meeting_access_request_description",
            default = u"This meeting is invite only. That means that a mail will be sent with an access ticket. Contact meeting moderators for more information.")
    api.flash_messages.add(msg)
    url = resource_url(api.root, request)
    return HTTPFound(location=url)
