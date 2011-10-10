import re
from uuid import uuid4

from repoze.folder import Folder
from repoze.folder import unicodify
from zope.component import getUtility
from zope.interface import implements
from BTrees.OOBTree import OOBTree

from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.security_aware import SecurityAware
from voteit.core.models.date_time_util import utcnow
import colander

#FIXME: This should be changable some way.
#Things that should never be saved
RESTRICTED_KEYS = ('csrf_token', )


class BaseContent(Folder, SecurityAware):
    __doc__ = IBaseContent.__doc__
    implements(IBaseContent)
    add_permission = None
    content_type = None
    allowed_contexts = ()

    def __init__(self, **kwargs):
        #FIXME: Compat with betahaus.pyracont.BaseFolder
        self.uid = uuid4()
        self.created = utcnow()
        self.set_field_appstruct(kwargs)
        super(BaseContent, self).__init__()

    @property
    def _storage(self):
        storage = getattr(self, '__storage__', None)
        if storage is None:
            storage = self.__storage__ =  OOBTree()
        return storage

    def get_field_value(self, key, default=None):
        """ Get value. Return default if it doesn't exist. """
        return self._storage.get(key, default)

    def set_field_value(self, key, value):
        """ Store value in 'key' in annotations. """
        if key in RESTRICTED_KEYS:
            return
        self._storage[key] = value

    def get_field_appstruct(self, schema):
        """ Get an appstruct from the current field values.
            Appstruct is just a dictionary. Deform can use it to populate existing fields.
            The trick with marker is to make sure that None is handled properly.
        """
        marker = object()
        appstruct = {}
        for field in schema:
            value = self.get_field_value(field.name, marker)
            if value != marker:
                appstruct[field.name] = value
        return appstruct

    def set_field_appstruct(self, appstruct):
        updated = set()
        for (k, v) in appstruct.items():
            if k in RESTRICTED_KEYS:
                continue
            if self.get_field_value(k) != v:
                self.set_field_value(k, v)
                updated.add(k)
        return updated

    #uid
    def _get_uid(self):
        return getattr(self, '__UID__', None)
    
    def _set_uid(self, value):
        self.__UID__ = unicodify(value)
        
    uid = property(_get_uid, _set_uid)

    #title
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

    #creators
    def _get_creators(self):
        return getattr(self, '__creators__', ())

    def _set_creators(self, value):
        self.__creators__ = tuple(value)
    
    creators = property(_get_creators, _set_creators)

    def get_content(self, content_type=None, iface=None, states=None, sort_on=None, sort_reverse=False, limit=None):
        """ See IBaseContent """
        results = set()

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
            
            results.add(candidate)

        if sort_on is None:
            return tuple(results)
        
        def _sorter(obj):
            return getattr(obj, sort_on)

        results = tuple(sorted(results, key = _sorter, reverse = sort_reverse))
        
        if limit:
            results = results[-limit:]

        return results
