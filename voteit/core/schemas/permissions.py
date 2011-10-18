import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from pyramid.traversal import find_root

from voteit.core.validators import deferred_existing_userid_validator
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.security import MEETING_ROLES
from voteit.core.security import ROOT_ROLES
from voteit.core import VoteITMF as _


@colander.deferred
def deferred_autocompleting_userid_widget(node, kw):
    context = kw['context']
    root = find_root(context)
    choices = tuple(root.users.keys())
    return deform.widget.AutocompleteInputWidget(
        size=30,
        values = choices,
        min_length=1)


@colander.deferred
def deferred_roles_widget(node, kw):
    """ Only handles role-like groups with prefix 'role:'"""
    context = kw['context']
    if ISiteRoot.providedBy(context):
        roles_choices = ROOT_ROLES
    elif IMeeting.providedBy(context):
        roles_choices = MEETING_ROLES
    else:
        TypeError("Wrong context for deferred_roles_widget - must be IMeeting or ISiteRoot.")
    return deform.widget.CheckboxChoiceWidget(values=roles_choices,
                                              missing=colander.null,)


class UserIDAndGroupsSchema(colander.Schema):
    userid = colander.SchemaNode(
        colander.String(),
        title = _(u"UserID"),
        validator=deferred_existing_userid_validator,
        widget = deferred_autocompleting_userid_widget,
    )
    #It's called groups here, but we restrict choices to roles only
    groups = colander.SchemaNode(
        deform.Set(allow_empty=True),
        title = _(u"Groups"),
        widget=deferred_roles_widget,
    )


class UserIDsAndGroupsSequenceSchema(colander.SequenceSchema):
    userid_and_groups = UserIDAndGroupsSchema(title=_(u'Roles for user'),)


@schema_factory('PermissionsSchema')
class PermissionsSchema(colander.Schema):
    userids_and_groups = UserIDsAndGroupsSequenceSchema(title=_(u'Role settings for users'))

