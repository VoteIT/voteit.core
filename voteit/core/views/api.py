from time import strftime

from pyramid.renderers import get_renderer, render
from pyramid.security import authenticated_userid
from pyramid.security import principals_allowed_by_permission
from pyramid.url import resource_url
from pyramid.location import lineage, inside
from pyramid.traversal import find_root, find_interface

from voteit.core.models.factory_type_information import ftis
from voteit.core.models.meeting import Meeting


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
        self.navigation = get_renderer('templates/navigation.pt').implementation()
        self.lineage = lineage(context)
        rev = []
        [rev.insert(0, x) for x in self.lineage]
        self.reversed_lineage = tuple(rev)
        self.inside = inside


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

    #navigation stuff
    def find_meeting(self, context):
        """ Is the current context inside a meeting, or a meeting itself? """
        return find_interface(context, Meeting)

    def get_content(self, context, content_type=None):
        """ Get contained items.
            If a content_type is passed, it will restrict the search to that type.
        """
        if content_type is None:
            return context.values()
        return [x for x in context.values() if x.content_type == content_type]

    def get_action_bar(self, context, request):
        """ Get the action-bar for a specific context """
        response = {}
        response['addable_types'] = self._get_addable_types(context)
        response['context'] = context
        return render('templates/action_bar.pt', response, request=request)
    