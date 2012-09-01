from deform import Form
from deform.exception import ValidationFailure
from pyramid.view import view_config
from pyramid.traversal import find_resource
from pyramid.traversal import resource_path
from pyramid.security import Everyone
from pyramid.security import effective_principals
from repoze.catalog.query import Eq
from repoze.catalog.query import Any
from repoze.catalog.query import Contains
from repoze.catalog.query import Name
from betahaus.pyracont.factories import createSchema
from zope.index.text.parsetree import ParseError

from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.schemas import button_search
from voteit.core.models.schemas import add_csrf_token
from voteit.core.security import VIEW
from voteit.core.helpers import strip_and_truncate
from voteit.core import VoteITMF as _


SEARCH_VIEW_QUERY = Eq('path', Name('path')) \
    & Contains('searchable_text', Name('searchable_text')) \
    & Any('content_type', ('DiscussionPost', 'Proposal', 'AgendaItem' )) \
    & Any('allowed_to_view', Name('allowed_to_view'))


class SearchView(BaseView):
    """ Handle incoming search query and display result. """

    @view_config(context=IMeeting, name="search", renderer="templates/search.pt", permission = VIEW)
    def search(self):
        schema = createSchema('SearchSchema').bind(context = self.context, request = self.request)
        add_csrf_token(self.context, self.request, schema)        
        form = Form(schema, buttons=(button_search,))
        self.api.register_form_resources(form)
        appstruct = {}
        self.response['results'] = []

        def _results_ts(count):
            """ Note about the odd syntax: pluralize returns unicode, so it won't be translated.
                Hence it needs to be converted back to a translation string.
            """
            return _(self.api.pluralize(_(u"item"),
                                      _(u"items"),
                                      count))

        post = self.request.POST
        if 'search' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e: #pragma : no cover
                self.response['search_form'] = e.render()
                return self.response

            #Preform the actual search
            query = {}
            if appstruct['query']:
                query['searchable_text'] = appstruct['query']
            query['path'] = resource_path(self.api.meeting)
            if self.api.userid:
                query['allowed_to_view'] = effective_principals(self.request)
            else:
                query['allowed_to_view'] = [Everyone]

            cat_query = self.api.root.catalog.query
            get_metadata = self.api.root.catalog.document_map.get_metadata
            try:
                num, results = cat_query(SEARCH_VIEW_QUERY, names = query, sort_index = 'created', reverse = True)
                self.response['results'] = [get_metadata(x) for x in results]
            except ParseError, e:
                msg = _(u"search_exception_notice",
                        default = u"Search resulted in an error - it's not possible to search for common operator words like 'if' or 'the'.")
                self.api.flash_messages.add(msg, type = 'error')

        self.response['search_form'] = form.render(appstruct = appstruct)
        self.response['query_data'] = appstruct
        self.response['results_ts'] = _results_ts
        self.response['results_count'] = len(self.response['results'])
        self.response['strip_truncate'] = strip_and_truncate
        return self.response

