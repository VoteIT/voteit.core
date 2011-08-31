from time import strftime

from pyramid.renderers import get_renderer, render
from pyramid.security import authenticated_userid
from pyramid.security import Allowed
from pyramid.security import Authenticated
from pyramid.security import Everyone
from pyramid.url import resource_url
from pyramid.location import lineage
from pyramid.location import inside
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from pyramid.exceptions import Forbidden
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.decorator import reify
from pyramid.i18n import get_locale_name, get_localizer
from webob.exc import HTTPFound
from repoze.workflow import get_workflow
from webhelpers.html.converters import nl2br

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import IContentUtility
from voteit.core.models.interfaces import IDateTimeUtil
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ISQLSession
from voteit.core.models.log import Logs
from voteit.core.views.macros import FlashMessages
from voteit.core.views.expressions import ExpressionsView
from voteit.core.models.unread import Unreads
from voteit.core.models.message import Messages


class APIView(object):
    """ Convenience methods for templates """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request
        
        self.resource_url = resource_url
        self.root = find_root(context)
        self.sql_session = request.registry.getUtility(ISQLSession)()

        #Authentication- / User-related
        self.userid = authenticated_userid(request)
        if self.userid:
            self.user_profile = self.get_user(self.userid)
            self.user_profile_url = resource_url(self.user_profile, request)
            self.messages_adapter = Messages(self.sql_session)
        
        #Only in meeting context
        if self.userid and self.meeting:
            self.msg_count = self.messages_adapter.unreadcount_in_meeting(self.meeting.uid, self.userid)
                
        #Authentication / Authorization utils. 
        self.authn_policy = request.registry.getUtility(IAuthenticationPolicy)
        self.authz_policy = request.registry.getUtility(IAuthorizationPolicy)

        #request.application_url
        self.main_template = get_renderer('templates/main.pt').implementation()
        self.content_info = request.registry.getUtility(IContentUtility)
        self.addable_types = self._get_addable_types(context, request)
        self.lineage = lineage(context)
        rev = []
        [rev.insert(0, x) for x in self.lineage]
        self.reversed_lineage = tuple(rev)
        self.inside = inside
        self.dt_util = request.registry.getUtility(IDateTimeUtil)

        #macros
        self.flash_messages = FlashMessages(request)
        self.expressions = ExpressionsView(request)
        
        self.logs = Logs(self.sql_session)
        
        self.nl2br = nl2br
        
        self.locale = get_locale_name(request)

    def translate(self, *args, **kwargs):
        """ Hook into the translation string machinery.
            See the i18n section of the Pyramid Docs.
        """ 
        return _(*args, **kwargs)

    def _get_user_cache(self):
        cache = getattr(self.request, '_user_lookup_cache', None)
        if cache is None:
            cache = self.request._user_lookup_cache = {}
        return cache

    def get_user(self, userid):
        """ Returns the user object. Will also cache each lookup. """
        cache = self._get_user_cache()
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
                self.context_has_permission(type.add_permission, self.context):
                addable_names.add(type.type_class.content_type)
        return tuple(addable_names)
        
    @reify
    def meeting(self):
        """ Is the current context inside a meeting, or a meeting itself? """
        return find_interface(self.context, IMeeting)

    def _is_section_closed(self, section):
        return self.request.cookies.get(section, None)

    def get_navigation(self):
        """ Get navigatoin """

        response = {}
        response['api'] = self
        response['context_has_permission'] = self.context_has_permission
        if self.meeting:
            response['is_moderator'] = self.context_has_permission(security.MODERATE_MEETING, self.meeting)
        else:
            response['is_moderator'] = False
        if response['is_moderator']:
            response['sections'] = ('closed', 'active', 'inactive', 'private')
        else:
            response['sections'] = ('closed', 'active', 'inactive')
        response['is_closed'] = self._is_section_closed
        
        return render('templates/navigation.pt', response, request=self.request)

    def get_action_bar(self, context, request):
        """ Get the action-bar for a specific context """

        def _show_retract():
            return context.content_type == 'Proposal' and \
                self.context_has_permission('Retract', context) and \
                context.get_workflow_state() == 'published'
        
        response = {}
        response['api'] = self
        response['addable_types'] = self._get_addable_types(context, request)
        response['context'] = context
        if getattr(context, 'workflow', None):
            response['states'] = context.get_available_workflow_states(request)
        response['context_has_permission'] = self.context_has_permission
        response['show_retract'] = _show_retract
        response['is_moderator'] = self.context_has_permission(security.MODERATE_MEETING, context)
        
        return render('templates/action_bar.pt', response, request=request)

    def get_profile_toolbar(self, context, request):
        return render('templates/profile_toolbar.pt', {'api':self}, request=request)

    def get_time_info(self, context, request):
        """ Render start and end time of something, if those exist. """
        response = {}
        response['dt_format'] = self.dt_util.dt_format
        response['start_time'] = context.get_field_value('start_time')
        response['end_time'] = context.get_field_value('end_time')
        return render('templates/time_info.pt', response, request=request)
        
    def get_time_created(self, context):
        """ Render start and end time of something, if those exist. """
        return self.dt_util.d_format(context.created)

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

    def context_has_permission(self, permission, context):
        """ Special permission check that is agnostic of the request.context attribute.
            (As opposed to pyramid.security.has_permission)
            Don't use anything else than this one to determine permissions for something
            where the request.context isn't the same as context, for instance another 
            object that appears in a listing.
        """
        principals = self.context_effective_principals(context)
        return self.authz_policy.permits(context, principals, permission)

    def context_effective_principals(self, context):
        """ Special version of pyramid.security.effective_principals that
            adds groups based on context instead of request.context
        """
        effective_principals = [Everyone]
        if self.userid is None:
            return effective_principals
        
        groups = context.get_groups(self.userid)
        
        effective_principals.append(Authenticated)
        effective_principals.append(self.userid)
        effective_principals.extend(groups)
        
        return effective_principals
        
    def get_unread(self, context, content_type=None):
        unreads = Unreads(self.sql_session)
        contents = context.get_content(content_type=content_type)
        unread_count = 0
        for content in contents:
            if len(unreads.retrieve(self.userid, content.uid)) > 0:
                unread_count = unread_count+1
            
        return unread_count
        
    def is_unread(self, context, mark=False):
        unreads = Unreads(self.sql_session)
        unread_items = unreads.retrieve(self.userid, context.uid)
        if unread_items:
            # there should only be one anyways
            for unread_item in unread_items:
                if mark and not unread_item.persistent:
                    unreads.remove(self.userid, context.uid)
            
            return True
            
        return False
        
    def get_restricted_content(self, context, content_type=None, iface=None, states=None, sort_on=None, sort_reverse=False):
        candidates = context.get_content(content_type=content_type, iface=iface, states=states, sort_on=sort_on, sort_reverse=sort_reverse)
        results = []
        for candidate in candidates:
            if self.context_has_permission(security.VIEW, candidate):
                results.append(candidate)
            
        return results
