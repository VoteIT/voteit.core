from pyramid.view import view_config
from pyramid.traversal import resource_path, find_resource

from repoze.catalog.query import Eq
from repoze.catalog.query import Contains
from repoze.catalog.query import Name

from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core import VoteITMF as _

SEARCH_VIEW_QUERY = Eq('path', Name('path')) & Contains('searchable_text', Name('searchable_text'))


class SearchView(BaseView):
    """ Handle incoming search query and display result. """
    
    @view_config(context=IMeeting, name="search", renderer="templates/search_result.pt")
    def search_view(self):
        search_string = self.request.params.get('query')
        self.response['search_string'] = search_string #Could be None
        self.response['search_results'] = ()

        if not search_string:
            return self.response
        
        meeting = self.api.meeting
        cat_query = self.api.root.catalog.query
        docid_to_address = self.api.root.catalog.document_map.docid_to_address
        
        query_params = {}
        query_params['searchable_text'] = search_string
        query_params['path'] = resource_path(meeting)

        #FIXME: PERMISSION
        num, results = cat_query(SEARCH_VIEW_QUERY, names = query_params)

        if not num:
            return self.response
        
        objects = []

        for id in results:
            path = docid_to_address.get(id)
            obj = find_resource(meeting, path)
            if obj is not None:
                objects.append(obj)
        
        self.response['search_results'] = tuple(objects)
        
        return self.response