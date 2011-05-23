from time import strftime

from pyramid.renderers import get_renderer, render
from pyramid.security import authenticated_userid, has_permission
from pyramid.url import resource_url
from pyramid.location import lineage, inside
from pyramid.traversal import find_root, find_interface
from webob.exc import HTTPFound
from pyramid.exceptions import Forbidden

from repoze.workflow import get_workflow

from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IContentUtility
from voteit.core.models.expression_adapter import Expressions


class APIView(object):
    """ Convenience methods for templates """
    USER_CACHE_ATTR = '_user_lookup_cache'
        
    def __init__(self, context, request):
        self.context = context
        self.request = request
        
        self.resource_url = resource_url
        self.root = find_root(context)
        setattr(self, self.USER_CACHE_ATTR, {})

        #Authentication- / User-related
        self.userid = authenticated_userid(request)
        if self.userid:
            self.user_profile = self.get_user(self.userid)
            self.user_profile_url = resource_url(self.user_profile, request)
        
        #request.application_url
        self.main_template = get_renderer('templates/main.pt').implementation()
        self.content_info = request.registry.getUtility(IContentUtility)
        self.addable_types = self._get_addable_types(context, request)
        self.navigation = get_renderer('templates/navigation.pt').implementation()
        self.profile_toolbar = get_renderer('templates/profile_toolbar.pt').implementation()
        self.lineage = lineage(context)
        rev = []
        [rev.insert(0, x) for x in self.lineage]
        self.reversed_lineage = tuple(rev)
        self.inside = inside
        

    def get_user(self, userid):
        """ Returns the user object. Will also cache each lookup. """
        cache = getattr(self, self.USER_CACHE_ATTR)
        if userid in cache:
            return cache[userid]
        
        user = self.root.users.get(userid)
        cache[userid] = user
        return user

    def format_feed_time(self, value):
        """ Lordag 3 apr 2010, 01:10
        """
        return strftime("%A %d %B %Y, %H:%M", value)
    
    def _get_addable_types(self, context, request):
        context_type = getattr(context, 'content_type', '')
        if not context_type:
            return ()
        
        addable_names = set()
        for type in self.content_info.values():
            if context_type in type.allowed_contexts and \
                has_permission(type.add_permission, context, request):
                addable_names.add(type.type_class.content_type)
        return tuple(addable_names)

    #navigation stuff
    def find_meeting(self, context):
        """ Is the current context inside a meeting, or a meeting itself? """
        return find_interface(context, IMeeting)

    def get_content(self, context, **kwargs):
        """ Get contained items.
            If a content_type is passed, it will restrict the search to that type.
            See models/IBaseContent
        """
        return tuple(context.get_content(**kwargs))

    def get_action_bar(self, context, request):
        """ Get the action-bar for a specific context """
        response = {}
        response['addable_types'] = self._get_addable_types(context, request)
        response['context'] = context
        response['resource_url'] = resource_url        
        response['states'] = context.get_available_workflow_states()

        return render('templates/action_bar.pt', response, request=request)

    def get_creators_info(self, creators, request):
        """ Return template for a set of creators.
            The content of creators should be userids
        """
        
        users = set()
        for userid in creators:
            user = self.get_user(userid)
            if user:
                users.add(user)
        
        response = {}
        response['resource_url'] = resource_url
        response['users'] = users
        return render('templates/creators_info.pt', response, request=request)

    def get_user_expressions(self, context, tag, userid, display_name=None):
        expressions = Expressions(self.request)
        userids = expressions.retrieve_userids(tag, context.uid)

        response = {}
        response['context_id'] = context.uid
        response['toggle_url'] = "%sset_expression" % resource_url(context, self.request)
        response['tag'] = tag
        response['display_name'] = display_name
        response['button_txt'] = "%s %s" % (len(userids), display_name and display_name or tag)
        
        if userid and userid in userids:
            response['selected'] = True
            response['do'] = "0"
        else:
            response['selected'] = False
            response['do'] = "1"
        response['count'] = len(userids)
                
        return render('templates/user_expressions.pt', response, request=self.request)
