from pkg_resources import resource_filename

from pyramid.location import lineage
from pyramid.security import authenticated_userid
from pyramid.url import resource_url
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from pyramid.traversal import find_resource
from pyramid.traversal import resource_path
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.decorator import reify
from pyramid.i18n import get_localizer
from betahaus.pyracont.interfaces import IContentFactory
from betahaus.viewcomponent import render_view_group
from betahaus.viewcomponent.interfaces import IViewGroup
from repoze.catalog.query import Eq
from repoze.catalog.query import Any
from webhelpers.html.tools import auto_link
from webhelpers.html.converters import nl2br
from webhelpers.html.render import sanitize

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.interfaces import IDateTimeUtil
from voteit.core.models.interfaces import IFanstaticResources
from voteit.core.models.interfaces import IFlashMessages
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.catalog import metadata_for_query
from voteit.core.models.catalog import resolve_catalog_docid
from voteit.core.fanstaticlib import DEFORM_RESOURCES
from voteit.core.helpers import at_userid_link
from voteit.core.helpers import tags2links


TEMPLATE_DIR = resource_filename('voteit.core.views', 'templates/')

class APIView(object):
    """ Convenience methods for templates """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.resource_url = resource_url
        self.userid = authenticated_userid(request)
        self.template_dir = TEMPLATE_DIR
        self.tag_count = {}

    @reify
    def root(self):
        return find_root(self.context)

    @reify
    def authn_policy(self):
        """ Registered authentication policy. """
        return self.request.registry.getUtility(IAuthenticationPolicy)

    @reify
    def authz_policy(self):
        """ Registered authorization policy. """
        return self.request.registry.getUtility(IAuthorizationPolicy)

    @reify
    def dt_util(self):
        """ The datetime conversion utility.
            See :mod:`voteit.core.interfaces.IDateTimeUtil` for docs.
        """
        return self.request.registry.getUtility(IDateTimeUtil)

    @property
    def user_profile(self):
        """ Get currently authenticated users profile, or None.
            get_user caches lookup so this is a regular property.
        """
        return self.get_user(self.userid)

    @reify
    def flash_messages(self):
        """ Flash messages adapter - stores and retrieves messages.
            See :mod:`voteit.core.models.interfaces.IFlashMessages`
        """
        return self.request.registry.getAdapter(self.request, IFlashMessages)

    @reify
    def show_moderator_actions(self):
        """ Show moderator actions? Falls back to MANAGE_SERVER if outside of
            a meeting context.
        """
        if self.meeting is None:
            return self.context_has_permission(security.MANAGE_SERVER, self.root)
        return self.context_has_permission(security.MODERATE_MEETING, self.meeting)

    @reify
    def localizer(self):
        """ Get the current localizer. See the Pyramid docs for more on localizers.
        """
        return get_localizer(self.request)

    @reify
    def cached_effective_principals(self):
        """ Effective principals for the view that APIView was wrapped with. self.context in other words, should always
            be same as request.context.
        """
        return self.context_effective_principals(self.context)

    @property
    def translate(self):
        """ Translate a translation string immediately. """
        return self.localizer.translate

    @property
    def pluralize(self):
        """ pluralize(singular, plural, n, domain=None, mapping=None)
            Where n is amount of something.
            See pluralize in the Pyramid docs.
        """
        return self.localizer.pluralize

    @reify
    def context_unread(self):
        """ All docids of things that are unread contained in this context. """
        if not self.userid:
            return ()
        return self.search_catalog(context = self.context, unread = self.userid)[1]

    @reify
    def breadcrumbs(self):
        """ Get objects from root and out, so we can iterate over them and get links etc. """
        return reversed(tuple(lineage(self.context)))

    @reify
    def custom_logo_tag(self):
        url = None
        if self.meeting:
            url = self.meeting.get_field_value('meeting_logo_url')
        if not url:
            url = self.root.get_field_value('default_logo_url')
        if url:
            return u'<img src="%s" id="meeting-logo" alt="Meeting logo" />' % url

    def register_form_resources(self, form):
        """ Append form resources if they don't already exist in self.form_resources """
        for (key, version) in form.get_widget_requirements():
            for resource in DEFORM_RESOURCES.get(key, ()):
                resource.need()
            #FIXME: Otherwise log error

    def include_needed(self, context, request, view):
        """ Include needed :term:`Fanstatic` resources.
            See :mod:`voteit.core.models.interfaces.IFanstaticResources` for more
            info on dealing with the resource utility.
        """
        util = request.registry.getUtility(IFanstaticResources)
        util.include_needed(context, request, view)

    def tstring(self, *args, **kwargs):
        """ Hook into the translation string machinery.
            See the i18n section of the Pyramid Docs.
            This is usefull when you don't want any i18n tool to pick it up in the code,
            for instance when you're converting the contents of a variable.
        """ 
        return _(*args, **kwargs)

    def get_user(self, userid):
        """ Returns the user object. Will also cache each lookup.
            Reason for the try/except code is execution speed.
        """
        try:
            cache = self.request._user_lookup_cache
        except AttributeError:
            self.request._user_lookup_cache = cache = {}
        try:
            return cache[userid]
        except KeyError:
            user = self.root.users.get(userid)
            cache[userid] = user
            return user

    @reify
    def meeting(self):
        """ Is the current context inside a meeting, or a meeting itself? """
        return find_interface(self.context, IMeeting)

    @reify
    def meeting_state(self):
        """ Current wf state of meeting if you're inside a meeting. """
        if self.meeting:
            return self.meeting.get_workflow_state()

    @reify
    def meeting_url(self):
        """ Cache lookup of meeting url since it will be used a lot. """
        if self.meeting:
            return resource_url(self.meeting, self.request)

    def get_moderator_actions(self, context):
        """ A.k.a. the cogwheel-menu. context might be a brain here, but the view component must have an object context."""
        if not IBaseContent.providedBy(context):
            #Assume brain - might need to change this later
            context = find_resource(self.root, context['path'])
        return self.render_single_view_component(context, self.request, 'main', 'moderator_actions')
        
    def get_time_created(self, context):
        """ Render start and end time of something, if those exist. """
        return self.dt_util.relative_time_format(context.created)

    def get_userinfo_url(self, userid):
        if self.meeting_url is None:
            raise ValueError("get_userinfo_url was called when api.meeting_url was None. Are you outside of a meeting context?")
        assert isinstance(userid, basestring)
        return "%s_userinfo?userid=%s" % (self.meeting_url, userid)

    def get_creators_info(self, creators, portrait = True):
        """ Return template for a set of creators.
            The content of creators should be userids.
        """
        return self.render_single_view_component(self.context, self.request, 'main', 'creators_info',
                                                 creators = creators, portrait = portrait)

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
        return security.context_effective_principals(context, self.userid)

    def is_brain_unread(self, brain):
        """ Check if a catalog metadata ("brain" object) is unread by the currently logged in user.
        """
        return brain['docid'] in self.context_unread
                
    def get_restricted_content(self, context, content_type=None, iface=None,
                               states=None, sort_on=None, sort_reverse=False):
        """ Use this method carefully. It might be pretty expensive to run. """
        candidates = context.get_content(content_type=content_type, iface=iface, states=states,
                                         sort_on=sort_on, sort_reverse=sort_reverse)
        results = []
        for candidate in candidates:
            if self.context_has_permission(security.VIEW, candidate):
                results.append(candidate)
            
        return results

    def search_catalog(self, context=None, **kwargs):
        """ Same as catalog.search, but also extracts path from context if it's specified.
            returns the same tuple with (itemcount, docid_set) as result.
            
            Note: search is deprecated in catalog so this will removed. Use query instead!
        """
        if context is not None:
            if 'path' in kwargs:
                ValueError("Can't specify both context and path")
            kwargs['path'] = resource_path(context)
        return self.root.catalog.search(**kwargs)

    def query_catalog(self, query, **kw):
        """ Return a tuple of (itemcount, docids). Query object is either a CQE or a string.
            Check repoze.catalog documentation for usage.
        """
        return self.root.catalog.query(query, **kw)

    def resolve_catalog_docid(self, docid):
        """ Take a catalog docid and fetch its object. Convenience wrapper for api view"""
        return resolve_catalog_docid(self.root.catalog, self.root, docid)

    def get_metadata_for_query(self, **kwargs):
        """ Return metadata for catalog search result. """
        return metadata_for_query(self.root.catalog, **kwargs)

    def get_content_factory(self, content_type):
        """ Content factory of a content type. This is a utility that is
            responsible for the construction of new content. Something like this:

            .. code-block:: python

               factory = get_content_factory('AgendaItem')
               new_agenda_item = factory(title = 'New title for Agenda item')
        """
        return self.request.registry.getUtility(IContentFactory, name=content_type)

    def content_types_add_perm(self, content_type):
        """ Add permission for a specific content type. It's the value specified as
            'add_permission' on the contents class. Anything normally addable by someone
            will have this attribute. See content in models.
        """
        factory = self.get_content_factory(content_type)
        return getattr(factory._callable, 'add_permission', None)

    def get_schema_name(self, content_type, action):
        """ Each content type normally has schemas registered for actions like edit and add.
            This is a convenience method for quick lookup of those schemas. It will the return
            the factory name of the schema registered for a specific action.

            Example:

            .. code-block:: python

               import colander
               from betahaus.pyracont.decorators import content_factory
               from betahaus.pyracont.decorators import schema_factory


               @content_factory('DummyContent', title=u"Dummy things")
               class DummyContent(object):
                   schemas = {'edit': 'EditSchema', 'add': 'AddSchema'}

               @schema_factory('EditSchema', title=u"Edit me")
               class EditSchema(colander.Schema)
                   dummy = colander.SchemaNode(colander.String())

            If you would run get_schema_name('DummyContent', 'edit') it would return the string 'EditSchema'
            which can be used to construct a schema with createSchema.

            If things go wrong:
            * ComponentLookupError if content_type doesn't exist
            * KeyError if action doesn't exist.
        """
        factory = self.get_content_factory(content_type)
        return factory._callable.schemas[action]

    def render_view_group(self, context, request, name, **kw):
        if 'api' not in kw:
            kw['api'] = self
        return render_view_group(context, request, name, **kw)

    def render_single_view_component(self, context, request, group, key, **kw):
        util = request.registry.getUtility(IViewGroup, name = group)
        if 'api' not in kw:
            kw['api'] = self
        return util[key](context, request, **kw)

    def transform(self, text):
        text = sanitize(text)
        text = auto_link(text, link='urls')
        text = nl2br(text)
        if self.meeting.get_field_value('tags_enabled', True): #FIXME: Lookup everytime + breaks outside of meetings...
            text = tags2links(unicode(text), self)
        text = at_userid_link(text, self.context, self.request)
        return text

    def get_tag_count(self, tag):
        """ Returns total count for a tag withing the context this view was registered on. """
        try:
            return self.tag_count[tag]
        except KeyError:
            query = Eq('path', resource_path(self.context)) &\
                    Any('allowed_to_view', self.cached_effective_principals) &\
                    Any('tags', tag)
            self.tag_count[tag] = self.root.catalog.query(query)[0]
            return self.tag_count[tag]
