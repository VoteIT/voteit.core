""" Common schema methods """
import colander
import deform
from pyramid.exceptions import Forbidden

from voteit.core import VoteITMF as _


def add_csrf_token(context, request, schema):
    token = request.session.get_csrf_token()
    
    def _validate_csrf(node, value):
        if value != token:
            #Normally this raises colander.Invalid, but that error will be
            #hidden since the form element for csrf is hidden.
            #The error as such should only appear if someone is actually
            #beeing attacked, so treating it like an input error seems wrong.
            raise Forbidden(_(u"CSRF token didn't match. Did you submit this yourself?"))
    
    schema.add(colander.SchemaNode(
                   colander.String(),
                   name="csrf_token",
                   widget = deform.widget.HiddenWidget(),
                   missing = u'',
                   default = token,
                   validator = _validate_csrf,
                   )
               )
