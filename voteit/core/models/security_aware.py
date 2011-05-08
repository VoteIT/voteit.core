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

    def update_from_form(self, value):
        """ Set permissions from a list of dicts with the following layout:
            {'userid':<userid>,'groups':<set of groups that the user should have>}.
        """
        #Unset all permissions from users that have them but didn't exist in the submitted form
        submitted_userids = [x['userid'] for x in value]
        for userid in self._groups:
            if userid not in submitted_userids:
                del self._groups[userid]
        
        #Set the new permissions
        for item in value:
            self.set_groups(item['userid'], item['groups'])

    def get_security_appstruct(self):
        """ Return the current settings in a structure that is usable in a deform form.
        """
        appstruct = {}
        userids_and_groups = []
        for userid in self._groups:
            userids_and_groups.append({'userid':userid, 'groups':self.get_groups(userid)})
        appstruct['userids_and_groups'] = userids_and_groups
        return appstruct

    def _check_groups(self, groups):
        for group in groups:
            if not group.startswith(NAMESPACES):
                raise ValueError('Groups need to start with either "group:" or "role:"')

    def list_all_groups(self):
        """ Returns a set of all groups in this context. """
        groups = set()
        [groups.update(x) for x in self._groups.values()]
        return groups

ROOT_ROLES = ((security.ROLE_ADMIN, _(u'Administrator'),))
MEETING_ROLES = ((security.ROLE_MODERATOR, _(u'Moderator')),
                 (security.ROLE_PARTICIPANT, _(u'Participant')),
                 (security.ROLE_VOTER, _(u'Voter')),
                 (security.ROLE_VIEWER, _(u'View only')),
                )


def get_groups_schema(context):
    """ Return selectable groups schema. This can be done in a smarter way with
        deferred schemas, but it can be like this for now.
    """
    root = find_root(context)
    user_choice = tuple(root.users.keys())
    userid_widget = deform.widget.AutocompleteInputWidget(
        size=10,
        values = user_choice,
        )
    if context is root:
        #Only show administrator as selectable group in root
        group_choices = ROOT_ROLES
    else:
        #In other contexts (like Meeting) meeting roles apply
        group_choices = MEETING_ROLES

    class UserIDAndGroupsSchema(colander.Schema):
        userid = colander.SchemaNode(
            colander.String(),
            validator=colander.OneOf(user_choice),
            widget = userid_widget,
            )
        groups = colander.SchemaNode(
            deform.Set(),
            widget=deform.widget.CheckboxChoiceWidget(values=group_choices),
            )
    
    class UserIDsAndGroupsSequenceSchema(colander.SequenceSchema):
        userid_and_groups = UserIDAndGroupsSchema(title=_(u'Groups for user'),)
    
    class Schema(colander.Schema):
        userids_and_groups = UserIDsAndGroupsSequenceSchema(title=_(u'Group settings for users'))
    
    return Schema()
