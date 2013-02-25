""" Common schema methods and buttons"""
import colander
import deform
from pyramid.exceptions import Forbidden

from voteit.core import VoteITMF as _
from voteit.core.schemas.common import add_csrf_token as new_csrf_func

#FIXME: Should this be here?

button_add = deform.Button('add', _(u"Add"))
button_cancel = deform.Button('cancel', _(u"Cancel"))
button_change = deform.Button('change', _(u"Change"))
button_delete = deform.Button('delete', _(u"Delete"))
button_login = deform.Button('login', _(u"Login"))
button_register = deform.Button('register', _(u"Register"))
button_request = deform.Button('request', _(u"Request"))
button_save = deform.Button('save', _(u"Save"))
button_update = deform.Button('update', _(u"Update"))
button_vote = deform.Button('vote', _(u"add_vote_button", default=u"Vote"))
button_resend = deform.Button('resend', _(u"Resend"))
button_download = deform.Button('download', _(u"Download"))
button_send = deform.Button('download', _(u"Send"))
button_search = deform.Button('search', _(u"Search"))

def add_csrf_token(context, request, schema):
    """ Deprecated, kept for backward compat."""
    return new_csrf_func(context, request, schema)

def add_came_from(context, request, schema):
    """ Add came from to schema."""
    referer = getattr(request, 'referer', '')

    schema.add(colander.SchemaNode(
                   colander.String(),
                   name="came_from",
                   widget = deform.widget.HiddenWidget(),
                   default = referer,
                   missing=u'',
                   )
               )