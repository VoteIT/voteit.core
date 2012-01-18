""" Common schema methods and buttons"""
import colander
import deform
from pyramid.exceptions import Forbidden

from voteit.core import VoteITMF as _

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


def add_csrf_token(context, request, schema):
    token = request.session.get_csrf_token()
    def _validate_csrf(node, value):
        if value != token:
            #Normally this raises colander.Invalid, but that error will be
            #hidden since the form element for csrf is hidden.
            #The error as such should only appear if someone is actually
            #beeing attacked, so treating it like an input error seems wrong.
            raise Forbidden("CSRF token didn't match. Did you submit this yourself?")
    
    schema.add(colander.SchemaNode(
                   colander.String(),
                   name="csrf_token",
                   widget = deform.widget.HiddenWidget(),
                   missing = u'',
                   default = token,
                   validator = _validate_csrf,
                   )
               )


