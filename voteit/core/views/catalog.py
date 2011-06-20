from pyramid.view import view_config
from pyramid.security import has_permission
from pyramid.exceptions import Forbidden

import colander
from deform import Form
from deform.exception import ValidationFailure
from webob.exc import HTTPFound
from pyramid.url import resource_url

from voteit.core.views.api import APIView
from voteit.core import VoteITMF as _
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.interfaces import ISiteRoot


class CatalogView(object):
    """ View class for adding, editing or deleting dynamic content. """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.response = {}
        self.response['api'] = self.api = APIView(context, request)

    @view_config(context=ISiteRoot, name="manage_catalog", renderer='templates/catalog.pt')
    def manage_catalog(self):

        schema = colander.Schema()
        add_csrf_token(self.context, self.request, schema)

        self.form = Form(schema, buttons=('cancel',))
        self.response['form_resources'] = self.form.get_widget_resources()

        post = self.request.POST
#        if 'update' in post:
#            controls = post.items()
#            try:
#                #appstruct is deforms convention. It will be the submitted data in a dict.
#                appstruct = self.form.validate(controls)
#                #FIXME: validate name - it must be unique and url-id-like
#            except ValidationFailure, e:
#                self.response['form'] = e.render()
#                return self.response
        
        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)
            
        self.response['form'] = self.form.render()
        self.response['catalog'] = self.api.root.catalog
        
        return self.response

