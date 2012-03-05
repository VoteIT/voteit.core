from deform import Form
from deform.exception import ValidationFailure
from pyramid.view import view_config
from pyramid.traversal import find_resource
from pyramid.traversal import resource_path
from repoze.catalog.query import Eq
from repoze.catalog.query import Contains
from repoze.catalog.query import Name
from betahaus.pyracont.factories import createSchema

from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.schemas import button_search
from voteit.core.models.schemas import add_csrf_token
from voteit.core import VoteITMF as _


SEARCH_VIEW_QUERY = Eq('path', Name('path')) & Contains('searchable_text', Name('searchable_text'))


class SearchView(BaseView):
    """ Handle incoming search query and display result. """
    
    @view_config(context=IMeeting, name="search", renderer="templates/search.pt")
    def search(self):
        schema = createSchema('SearchSchema').bind(context = self.context, request = self.request)
        add_csrf_token(self.context, self.request, schema)        
        form = Form(schema, buttons=(button_search,))
        self.api.register_form_resources(form)
        appstruct = {}
        self.response['results'] = []

        def _results_ts(count):
            return self.api.pluralize(_(u"item"),
                                      _(u"items"),
                                      count)

        post = self.request.POST
        if 'search' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['search_form'] = e.render()
                return self.response

            #Preform the actual search            
            #cat_query = self.api.root.catalog.query

            query = {}
            if appstruct['query']:
                query['searchable_text'] = appstruct['query']
            query['path'] = resource_path(self.api.meeting)
    
            #FIXME: PERMISSION
            #num, results = cat_query(SEARCH_VIEW_QUERY, names = query_params)

            self.response['results'] = self.api.get_metadata_for_query(**query)

        self.response['search_form'] = form.render(appstruct = appstruct)
        self.response['query_data'] = appstruct
        self.response['results_ts'] = _results_ts
        self.response['results_count'] = len(self.response['results'])
        return self.response









#        search_string = self.request.params.get('query')
#        self.response['search_string'] = search_string #Could be None
#        self.response['search_results'] = ()
#
#        if not search_string:
#            return self.response
#        
#        meeting = self.api.meeting
#        cat_query = self.api.root.catalog.query
#        docid_to_address = self.api.root.catalog.document_map.docid_to_address
#        
#        query_params = {}
#        query_params['searchable_text'] = search_string
#        query_params['path'] = resource_path(meeting)
#
#        #FIXME: PERMISSION
#        num, results = cat_query(SEARCH_VIEW_QUERY, names = query_params)
#
#        if not num:
#            return self.response
#        
#        objects = []
#
#        for id in results:
#            path = docid_to_address.get(id)
#            obj = find_resource(meeting, path)
#            if obj is not None:
#                objects.append(obj)
#        
#        self.response['search_results'] = tuple(objects)
#        
#        return self.response
