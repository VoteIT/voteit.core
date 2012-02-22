from logging import getLogger
from datetime import datetime

from betahaus.pyracont import BaseFolder
from zope.component.event import objectEventNotify
from zope.interface import implements
from pyramid.threadlocal import get_current_request
from pyramid.security import authenticated_userid
from repoze.folder import unicodify

from voteit.core.events import ObjectUpdatedEvent
from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.security_aware import SecurityAware
from voteit.core.security import ROLE_OWNER

#FIXME: This should be changable some way.
#Things that should never be saved
RESTRICTED_KEYS = ('csrf_token', )


class BaseContent(BaseFolder, SecurityAware):
    """ See :mod:`voteit.core.models.interfaces.IBaseContent`.
        All methods are documented in the interface of this class.
    """
    implements(IBaseContent)
    add_permission = None
    content_type = None
    allowed_contexts = ()
    schemas = {}

    def __init__(self, data=None, **kwargs):
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
                pass

        #Set owner - if it is in kwargs now
        if 'creators' in kwargs:
            userid = kwargs['creators'][0]
            #Don't send updated event on add
            self.add_groups(userid, (ROLE_OWNER,), event = False)

        super(BaseContent, self).__init__(data=data, **kwargs)

    def set_field_value(self, key, value):
        if key in RESTRICTED_KEYS:
            return
        super(BaseContent, self).set_field_value(key, value)

    def set_field_appstruct(self, values, notify=True, mark_modified=True):
        #Remove restricted keys, in case they're present
        #This might be changed to raise an error instead in time
        for restricted_key in RESTRICTED_KEYS:
            if restricted_key in values:
                del values[restricted_key]
        
        updated = super(BaseContent, self).set_field_appstruct(values, notify=notify, mark_modified=mark_modified)
        if updated and notify:
            objectEventNotify(ObjectUpdatedEvent(self, indexes=updated, metadata=True))
        return updated

    def _get_title(self):
        return self.get_field_value('title', u"")
    def _set_title(self, value):
        self.set_field_value('title', value)
    title = property(_get_title, _set_title)

    def _get_description(self):
        return self.get_field_value('description', u"")        
    def _set_description(self, value):
        self.set_field_value('description', value)
    description = property(_get_description, _set_description)

    def _get_creators(self):
        return self.get_field_value('creators', ())
    def _set_creators(self, value):
        value = tuple(value)
        self.set_field_value('creators', value)
    creators = property(_get_creators, _set_creators)
        
    def _get_created(self):
        return self.get_field_value('created', None)
    def _set_created(self, value):
        assert isinstance(value, datetime)
        self.set_field_value('created', value)
    created = property(_get_created, _set_created)
    
    def _get_modified(self):
        return self.get_field_value('modified', None)
    def _set_modified(self, value):
        assert isinstance(value, datetime)
        self.set_field_value('modified', value)
    modified = property(_get_modified, _set_modified)

    def _get_uid(self):
        return self.get_field_value('uid', None)
    def _set_uid(self, value):
        value = unicodify(value)
        self.set_field_value('uid', value)
    uid = property(_get_uid, _set_uid)

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
