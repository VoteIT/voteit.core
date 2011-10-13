from BTrees.OOBTree import OOBTree
from pyramid.location import lineage
from pyramid.traversal import find_root
from zope.interface import implements
import colander
import deform

from voteit.core.models.interfaces import ISecurityAware
from voteit.core import security
from voteit.core import VoteITMF as _


NON_INHERITED_GROUPS = ('role:Owner',)

ROLES_NAMESPACE = 'role:'
GROUPS_NAMESPACE = 'group:'
NAMESPACES = (ROLES_NAMESPACE, GROUPS_NAMESPACE, )


class SecurityAware(object):
    """ Mixin for all content that should handle groups.
        Principal in this terminology is a userid or a group id.
    """
    implements(ISecurityAware)

    @property
    def _groups(self):
        try:
            return self.__groups__
        except AttributeError:
            self.__groups__ = OOBTree()
            return self.__groups__
    
    def get_groups(self, principal):
        """ Return groups for a principal in this context.
            The special group "role:Owner" is never inherited.
        """
        groups = set()
        for location in lineage(self):
            location_groups = location._groups
            try:
                if self is location:
                    groups.update(location_groups[principal])
                else:
                    groups.update([x for x in location_groups[principal] if x not in NON_INHERITED_GROUPS])
            except KeyError:
                continue

        return tuple(groups)

    def check_groups(self, groups):
        """ Check dependencies and group names. """
        self._check_groups(groups)
        adjusted_groups = set()
        for group in groups:
            adjusted_groups.add(group)
            deps = security.ROLE_DEPENDENCIES.get(group, None)
            if deps is None:
                continue
            adjusted_groups.update(set(deps))

        return adjusted_groups

    def add_groups(self, principal, groups):
        """ Add a groups for a principal in this context.
        """
        groups = set(groups)
        groups.update(self.get_groups(principal))
        #Delegate check and set to set_groups
        self.set_groups(principal, groups)
    
    def set_groups(self, principal, groups):
        """ Set groups for a principal in this context. (This clears any previous setting)
            Will also take care of role dependencies.
        """
        if not groups:
            if principal in self._groups:
                del self._groups[principal]
            return
        adjusted_groups = self.check_groups(groups)
        self._groups[principal] = tuple(adjusted_groups)

    def get_security(self):
        """ Return the current security settings.
        """
        userids_and_groups = []
        for userid in self._groups:
            userids_and_groups.append({'userid':userid, 'groups':self.get_groups(userid)})
        return tuple(userids_and_groups)

    def set_security(self, value):
        """ Set current security settings according to value, that is a list of dicts with keys
            userid and groups. Will also clear any settings for users not present in value.
        """
        submitted_userids = [x['userid'] for x in value]
        current_userids = self._groups.keys()
        for userid in current_userids:
            if userid not in submitted_userids:
                del self._groups[userid]

        for item in value:
            self.set_groups(item['userid'], item['groups'])

    def _check_groups(self, groups):
        for group in groups:
            if not group.startswith(NAMESPACES):
                raise ValueError('Groups need to start with either "group:" or "role:"')

    def list_all_groups(self):
        """ Returns a set of all groups in this context. """
        groups = set()
        [groups.update(x) for x in self._groups.values()]
        return groups

