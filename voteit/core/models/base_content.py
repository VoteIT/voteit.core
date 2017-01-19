from datetime import datetime
import inspect
from uuid import uuid4

from BTrees.OOBTree import OOBTree
from arche.api import BaseMixin
from arche.resources import LocalRolesMixin
from arche.utils import utcnow
from pyramid.security import authenticated_userid
from pyramid.threadlocal import get_current_request
from repoze.folder import Folder
from repoze.folder import unicodify
from zope.component.event import objectEventNotify
from zope.interface import implementer

from voteit.core.events import ObjectUpdatedEvent
from voteit.core.models.interfaces import IBaseContent
from voteit.core.security import ROLE_OWNER

#FIXME: This should be changable some way.
#Things that should never be saved
RESTRICTED_KEYS = ('csrf_token', )

@implementer(IBaseContent)
class BaseContent(Folder, BaseMixin, LocalRolesMixin):
    """ See :mod:`voteit.core.models.interfaces.IBaseContent`.
        All methods are documented in the interface of this class.
        
        This also contains compatibility fixes between Arche and old VoteIT code.
    """
    add_permission = None
    default_view = u"view"
    nav_visible = True
    listing_visible = True
    search_visible = True
    custom_mutators = {} #<-- This is deprecated and will be removed
    custom_accessors = {} #<-- This is deprecated and will be removed

    def __init__(self, data=None, **kwargs):
        if 'creator' in kwargs and 'creators' not in kwargs:
            #Arche compat hack
            kwargs['creators'] = kwargs.pop('creator')
        if 'creators' not in kwargs:
            request = get_current_request()
            if request is None:
                #request will be None in some tests
                userid = None
            else:
                userid = authenticated_userid(request)
            if userid:
                kwargs['creators'] = (userid,)
            else:
                #FIXME: We'd like some sort of logging here,
                #but if we log in voteit.core, any poll plugin test will die very strangely
                #It has something with cleanup of logging in multithreading in setuptools
                pass #pragma : no cover
        #Set owner - if it is in kwargs now
        if 'creators' in kwargs:
            userid = kwargs['creators'][0]
            #Don't send updated event on add
            self.local_roles[userid] = (ROLE_OWNER,)
        if 'created' not in kwargs:
            kwargs['created'] = utcnow()
        if 'modified' not in kwargs:
            kwargs['modified'] = kwargs['created']
        if 'uid' not in kwargs:
            kwargs['uid'] = unicode(uuid4())
        super(BaseContent, self).__init__(data=data)
        self.set_field_appstruct(kwargs, notify = False, mark_modified = True)

    @property
    def field_storage(self):
        try:
            return self.__field_storage__
        except AttributeError:
            self.__field_storage__ = fs = OOBTree()
            return fs

    def set_field_value(self, key, value):
        """ Set field value.
            Will not send events, so use this if you silently want to change a single field.
            You can override field behaviour by either setting custom mutators
            or make a field a custom field.
        """
        if key in RESTRICTED_KEYS:
            return
        if key in self.custom_mutators:
            if inspect.stack()[2][3] == 'set_field_value':
                raise Exception("Custom mutator with key '%s' tried to call set_field_value." % key)
            mutator = self.custom_mutators[key]
            if isinstance(mutator, basestring):
                mutator = getattr(self, mutator)
            mutator(value, key=key)
            return
        self.field_storage[key] = value

    def set_field_appstruct(self, values, notify = True, mark_modified = True):
        #Remove restricted keys, in case they're present
        #This might be changed to raise an error instead in time
        for restricted_key in RESTRICTED_KEYS:
            if restricted_key in values:
                del values[restricted_key]
        updated = set()
        for (k, v) in values.items():
            cur = self.get_field_value(k)
            if cur == v:
                continue
            self.set_field_value(k, v)
            updated.add(k)
        if updated:
            updated.add('searchable_text') #Just to make sure
            updated.add('allowed_to_view')
            if mark_modified and 'modified' not in values:
                #Don't update if modified is set, since it will override the value we're trying to set.
                self.mark_modified()
                updated.add('modified')
            if 'tags' not in updated:
                #Hack to fix text
                updated.add('tags')
            if notify:
                #FIXME: This hack can be removed when transformations are live
                #Currently we need to reindex whenever some fields have changed
                objectEventNotify(ObjectUpdatedEvent(self, changed=updated))
        return updated

    @property
    def title(self):
        return self.get_field_value('title', u"")
    @title.setter
    def title(self, value):
        self.set_field_value('title', value)

    @property
    def description(self):
        return self.get_field_value('description', u"")
    @description.setter
    def description(self, value):
        self.set_field_value('description', value)

    def _get_creators(self):
        return self.get_field_value('creators', ())
    def _set_creators(self, value):
        value = tuple(value)
        self.set_field_value('creators', value)
    creators = property(_get_creators, _set_creators)
    creator = property(_get_creators, _set_creators) #Arche compat

    @property
    def created(self):
        return self.get_field_value('created', None)
    @created.setter
    def created(self, value):
        assert isinstance(value, datetime)
        self.set_field_value('created', value)

    @property
    def modified(self):
        return self.get_field_value('modified', None)
    @modified.setter
    def modified(self, value):
        assert isinstance(value, datetime)
        self.set_field_value('modified', value)

    @property
    def uid(self):
        return self.get_field_value('uid', '')
    @uid.setter
    def uid(self, value):
        self.set_field_value('uid', unicodify(value))

    def get_content(self, content_type=None, iface=None, states=None, sort_on=None, sort_reverse=False, limit=None):
        results = []
        for candidate in self.values():

            #Specific content_type?
            if content_type is not None:
                if getattr(candidate, 'content_type', '') != content_type:
                    continue

            #Specific interface?
            if iface is not None:
                if not iface.providedBy(candidate):
                    continue

            #Specific workflow state?
            if states is not None:
                #All objects might not have a workflow. In that case they won't have the method get_workflow_state
                try:
                    curr_state = candidate.get_workflow_state()
                    if isinstance(states, basestring):
                        #states is a string - a single state
                        if not curr_state == states:
                            continue
                    else:
                        #states is an iterable
                        if not curr_state in states:
                            continue
                except AttributeError:
                    continue
            
            results.append(candidate)

        if sort_on:
            def _sorter(obj):
                return getattr(obj, sort_on)
            results = sorted(results, key = _sorter, reverse = sort_reverse)
        
        if limit:
            results = results[-limit:]

        return tuple(results)

    @property
    def content_type(self): #b/c
        return self.type_name

    @property
    def display_name(self): #b/c
        return self.type_title

    def mark_modified(self):
        """ Mark content as modified. """
        self.modified = utcnow()

    def get_field_value(self, key, default=None):
        """ Return field value, or default """
        if key in self.custom_accessors:
            if inspect.stack()[2][3] == 'get_field_value':
                raise CustomFunctionLoopError("Custom accessor with key '%s' tried to call get_field_value." % key)
            accessor = self.custom_accessors[key]
            if isinstance(accessor, basestring):
                accessor = getattr(self, accessor)
            return accessor(default=default, key=key)
        return self.field_storage.get(key, default)

    def get_field_appstruct(self, schema):
        """ Return a dict of all fields and their values.
            Deform expects input like this when rendering already saved values.
            DEPRECATED - will be removed
        """
        marker = object()
        appstruct = {}
        for field in schema:
            value = self.get_field_value(field.name, marker)
            if value != marker:
                appstruct[field.name] = value
        return appstruct
