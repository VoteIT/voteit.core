from BTrees.OOBTree import OOBTree
from pyramid.location import lineage
from zope.interface import implements

from voteit.core.models.interfaces import ISecurityAware

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

    def add_groups(self, principal, groups):
        """ Add a groups for a principal in this context.
        """
        self._check_groups(groups)
        groups = set(groups)
        groups.update(self.get_groups(principal))
        self._groups[principal] = tuple(groups)
    
    def set_groups(self, principal, groups):
        """ Set groups for a principal in this context. (This clears any previous setting)
        """
        self._check_groups(groups)
        self._groups[principal] = tuple(groups)

    def _check_groups(self, groups):
        for group in groups:
            if not group.startswith(NAMESPACES):
                raise ValueError('Groups need to start with either "group:" or "role:"')
