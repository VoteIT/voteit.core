from time import strftime

from pyramid.renderers import get_renderer
from pyramid.security import authenticated_userid
from pyramid.security import principals_allowed_by_permission
from pyramid.url import resource_url
from pyramid.location import lineage
from pyramid.traversal import find_root

from voteit.core.models.factory_type_information import ftis


class APIView(object):
    """ Convenience methods for templates """
        
    def __init__(self, context, request):
        self.resource_url = resource_url
        self.userid = authenticated_userid(request)
        #request.application_url
        self.main_template = get_renderer('templates/main.pt').implementation()
        self.ftis = ftis
        self.addable_types = self._get_addable_types(context)
        self.root = find_root(context)
        
    def format_feed_time(self, value):
        """ Lordag 3 apr 2010, 01:10
        """
        return strftime("%A %d %B %Y, %H:%M", value)

    
    def _get_addable_types(self, context):
        context_type = getattr(context, 'content_type', '')
        if not context_type:
            return []
        
        addable_names = set()
        for type in self.ftis.values():
            if context_type in type.allowed_contexts:
                addable_names.add(type.type_class.content_type)
        return addable_names
