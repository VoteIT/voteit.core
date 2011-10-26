from pyramid.renderers import get_renderer, render
from pyramid.security import authenticated_userid
from pyramid.security import Authenticated
from pyramid.security import Everyone
from pyramid.url import resource_url
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from pyramid.traversal import resource_path
from pyramid.traversal import find_resource
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.decorator import reify
from webhelpers.html.converters import nl2br
from betahaus.pyracont.interfaces import IContentFactory
from betahaus.viewcomponent import render_view_group
from betahaus.viewcomponent.interfaces import IViewGroup

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.interfaces import IDateTimeUtil
from voteit.core.models.interfaces import IMeeting
from voteit.core.views.flash_messages import FlashMessages
from voteit.core.views.user_tags import UserTagsView
from voteit.core.models.catalog import metadata_for_query
from voteit.core.models.catalog import resolve_catalog_docid


MODERATOR_SECTIONS = ('closed', 'ongoing', 'upcoming', 'private',)
REGULAR_SECTIONS = ('closed', 'ongoing', 'upcoming',)


class APIView(object):
    """ Convenience methods for templates """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request
        
        self.resource_url = resource_url
        self.root = find_root(context)

        #Authentication- / User-related
        self.userid = authenticated_userid(request)
        if self.userid:
            self.user_profile = self.get_user(self.userid)
            self.user_profile_url = resource_url(self.user_profile, request)
        
        #Authentication / Authorization utils. 
        self.authn_policy = request.registry.getUtility(IAuthenticationPolicy)
        self.authz_policy = request.registry.getUtility(IAuthorizationPolicy)

        self.dt_util = request.registry.getUtility(IDateTimeUtil)

        #macros
        self.flash_messages = FlashMessages(request)
        
        self.nl2br = nl2br
        
        #Used by deform to keep track for form resources
        self.form_resources = {}
        #self.navigation_html = self._get_navigation()

        #Main macro
        self.main_template = get_renderer('templates/main.pt').implementation()

    @reify
    def show_moderator_actions(self):
        """ Show moderator actions? Falls back to MANAGE_SERVER if outside of
            a meeting context.
        """
        if self.meeting is None:
            return self.context_has_permission(security.MANAGE_SERVER, self.root)
        return self.context_has_permission(security.MODERATE_MEETING, self.meeting)

    @reify
    def user_tags_view(self):
        return UserTagsView(self.request)

    def register_form_resources(self, form):
        """ Append form resources if they don't already exist in self.form_resources """
        for (k, v) in form.get_widget_resources().items():
            if k not in self.form_resources:
                self.form_resources[k] = set()
            self.form_resources[k].update(v)

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

    def get_addable_types(self, context, request):
        context_type = getattr(context, 'content_type', '')
        if not context_type:
            return ()
        
        addable_names = set()
        for (name, factory) in request.registry.getUtilitiesFor(IContentFactory):
            if context_type not in getattr(factory._callable, 'allowed_contexts', ()):
                continue
            add_perm = getattr(factory._callable, 'add_permission', None)
            if add_perm is None:
                continue
            if not self.context_has_permission(add_perm, context):
                continue
            #Type is addable
            addable_names.add(name)
        return tuple(addable_names)

    @reify
    def meeting(self):
        """ Is the current context inside a meeting, or a meeting itself? """
        return find_interface(self.context, IMeeting)

    @reify
    def meeting_state(self):
        """ Current wf state of meeting if you're inside a meeting. """
        if not self.meeting:
            return
        return self.meeting.get_workflow_state()

    @reify
    def meeting_url(self):
        """ Cache lookup of meeting url since it will be used a lot. """
        if not self.meeting:
            return
        return resource_url(self.meeting, self.request)

    def get_global_actions(self, context, request):
        response = {}
        response['api'] = self
        response['meeting_time'] = self.dt_util.dt_format(self.dt_util.utcnow())
        return render('templates/global_actions.pt', response, request=request)

    def get_meeting_actions(self, context, request):
        response = {}
        response['api'] = self
        if self.userid:
            #Authenticated
            #Get available meetings outside of this context
            response['meetings'] = self.get_restricted_content(self.root, iface=IMeeting, sort_on='title')
            if self.meeting:
                #Sections
                if self.show_moderator_actions:
                    sections = MODERATOR_SECTIONS
                else:
                    sections = REGULAR_SECTIONS
                response['sections'] = sections

                #Metadata
                metadata = {}
                meeting_path = resource_path(self.meeting)
                show_polls = False
                for section in sections:
                    metadata[section] = self.get_metadata_for_query(content_type = 'Poll',
                                                                    path = meeting_path,
                                                                    workflow_state = section)
                    if metadata[section]:
                        show_polls = True
                response['show_polls'] = show_polls
                response['polls_metadata'] = metadata

                #Unread
                num, results = self.search_catalog(content_type = 'Poll', path = meeting_path, unread=self.userid)
                response['unread_polls_count'] = num

        response['is_moderator'] = self.context_has_permission(security.MODERATE_MEETING, context)

        return render('templates/meeting_actions.pt', response, request=request)

    def get_moderator_actions(self, context, request):
        """ A.k.a. the cogwheel-menu. """
        #If context is a brain, get the object
        if not IBaseContent.providedBy(context):
            #Assume brain
            context = find_resource(self.root, context['path'])
        response = {}
        response['api'] = self
        response['context'] = context
        if getattr(context, 'workflow', None):
            response['states'] = context.get_available_workflow_states(request)
        response['context_has_permission'] = self.context_has_permission
        response['is_moderator'] = self.context_has_permission(security.MODERATE_MEETING, context)
        return render('templates/moderator_actions.pt', response, request=request)
        
    def get_time_created(self, context):
        """ Render start and end time of something, if those exist. """
        return self.dt_util.relative_time_format(context.created)

    def get_userinfo_url(self, userid):
        if self.meeting_url is None:
            raise ValueError("get_userinfo_url was called when api.meeting_url was None. Are you outside of a meeting context?")
        assert isinstance(userid, basestring)
        return "%s_userinfo?userid=%s" % (self.meeting_url, userid)

    def get_creators_info(self, creators, request, portrait=True):
        """ Return template for a set of creators.
            The content of creators should be userids
        """
        #FIXME: Use view component and catalog query with metadata instead
        users = set()
        for userid in creators:
            user = self.get_user(userid)
            if user:
                users.add(user)
        response = {}
        response['users'] = users
        response['portrait'] = portrait
        response['get_userinfo_url'] = self.get_userinfo_url
        return render('templates/creators_info.pt', response, request=request)

    def get_poll_state_info(self, poll):
        response = {}
        response['api'] = self
        response['wf_state'] = poll.get_workflow_state()
        response['poll'] = poll
        return render('templates/poll_state_info.pt', response, request=self.request)

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
        
    def is_unread(self, context, mark=False):
        """ Check if something is unread. """
        if self.userid in context.get_unread_userids():
            if mark:
                context.mark_as_read(self.userid)
            return True
        return False
        
    def get_restricted_content(self, context, content_type=None, iface=None, states=None, sort_on=None, sort_reverse=False):
        """ Use this method carefully. It might be pretty expensive to run. """
        candidates = context.get_content(content_type=content_type, iface=iface, states=states, sort_on=sort_on, sort_reverse=sort_reverse)
        results = []
        for candidate in candidates:
            if self.context_has_permission(security.VIEW, candidate):
                results.append(candidate)
            
        return results

    def search_catalog(self, context=None, **kwargs):
        """ Same as catalog.search, but also extracts path from context if it's specified.
            returns the same tuple with (itemcount, docid_set) as result.
        """
        if context is not None:
            if 'path' in kwargs:
                ValueError("Can't specify both context and path")
            kwargs['path'] = resource_path(context)
        return self.root.catalog.search(**kwargs)

    def resolve_catalog_docid(self, docid):
        """ Take a catalog docid and fetch its object. Convenience wrapper for api view"""
        return resolve_catalog_docid(self.root.catalog, self.root, docid)

    def get_metadata_for_query(self, **kwargs):
        """ Return metadata for catalog search result. """
        return metadata_for_query(self.root.catalog, **kwargs)

    def get_content_factory(self, content_type):
        return self.request.registry.getUtility(IContentFactory, name=content_type)

    def content_types_add_perm(self, content_type):
        factory = self.get_content_factory(content_type)
        return getattr(factory._callable, 'add_permission', None)

    def get_schema_name(self, content_type, action):
        """ Will raise ComponentLookupError if content_type doesn't exist
            Will raise KeyError if action doesn't exist.
        """
        factory = self.get_content_factory(content_type)
        return factory._callable.schemas[action]

    def get_js_config_template(self):
        return render('templates/snippets/config.js.pt', {}, request=self.request)

    def render_view_group(self, context, request, name, **kw):
        if 'api' not in kw:
            kw['api'] = self
        return render_view_group(context, request, name, **kw)

    def render_single_view_component(self, context, request, group, key, **kw):
        util = request.registry.getUtility(IViewGroup, name = group)
        if 'api' not in kw:
            kw['api'] = self
        return util[key](context, request, **kw)
