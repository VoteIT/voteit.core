import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from pyramid.traversal import find_root

from voteit.core.validators import deferred_existing_userid_validator
from voteit.core.validators import deferred_context_roles_validator
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
        size=15,
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
    name = colander.SchemaNode(
        colander.String(),
        title = _(u"Name"),
        widget = deform.widget.TextInputWidget(template='readonly/textinput'),
        missing = u"",
    )
    #It's called groups here, but we restrict choices to roles only
    groups = colander.SchemaNode(
        deform.Set(allow_empty=True),
        title = _(u"Groups"),
        widget = deferred_roles_widget,
        validator = deferred_context_roles_validator,
    )


class UserIDsAndGroupsSequenceSchema(colander.SequenceSchema):
    userid_and_groups = UserIDAndGroupsSchema(title=_(u'Roles for user'),)


@schema_factory('PermissionsSchema',
                title = _(u"Permissions"),
                description = _(u"permissions_schema_main_description",
                                default = u"Set permission for each UserID that should have rights in this meeting. If you remove a UserID, their permissions will be cleared. View permission will be added automatically if needed for a higher permission - like Vote. Permissions also depend on the state of the meeting."))
class PermissionsSchema(colander.Schema):
    userids_and_groups = UserIDsAndGroupsSequenceSchema(title=_(u'Role settings for users'))


@schema_factory('SinglePermissionSchema',
                title = _(u"add_existing_user_to_meeting",
                          default = u"Add an existing user to this meeting"))
class SinglePermissionSchema(colander.Schema):
    userid = colander.SchemaNode(
        colander.String(),
        title = _(u"UserID"),
        description = _(u"single_permission_schema_userid_description",
                        default = u"Start typing the first letters of the UserID you want to add. You should see a popup below if that UserID exists."),
        validator=deferred_existing_userid_validator,
        widget = deferred_autocompleting_userid_widget,
    )
    #It's called groups here, but we restrict choices to roles only
    groups = colander.SchemaNode(
        deform.Set(allow_empty=True),
        title = _(u"Groups"),
        widget = deferred_roles_widget,
        validator = deferred_context_roles_validator,
    )
