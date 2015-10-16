# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from arche.interfaces import ISchemaCreatedEvent
from arche.schemas import current_userid_as_tuple
import colander
import deform

from voteit.core.schemas.proposal import ProposalSchema
from voteit.core.schemas.discussion_post import DiscussionPostSchema
from voteit.core.security import MODERATE_MEETING
from voteit.core import _


@colander.deferred
def add_as_system_user_widget(node, kw):
    #FIXME: This widget is less suitable than a regular select widget.
    #Figure out a smarter way to change data type returned, since we don't want a string
    request = kw['request']
    userids = list(request.meeting.system_userids)
    if userids:
        values = [(request.authenticated_userid, _("As yourself"))]
        for userid in userids:
            user = request.root['users'].get(userid, None)
            if user:
                values.append((userid, "%s (%s)" % (user.title, userid)))
        return deform.widget.SelectWidget(values = values, multiple = True)
    raise Exception("Widget shouldn't be loaded if there are no system_userids")
    
@colander.deferred
def current_user_or_system_users(node, kw):
    request = kw['request']
    values = [request.authenticated_userid]
    values.extend(request.meeting.system_userids)
    return colander.All(colander.ContainsOnly(values), colander.Length(min = 1, max = 1))

def to_tuple(value):
    #Since sets can't be indexed
    return tuple(value)

def system_users_in_add_schema(schema, event):
    """ Inject a choice so add a proposal as another user if:
        - The current user is a moderator
        - System users are set on the meeting
    """
    if event.request.has_permission(MODERATE_MEETING):
        system_userids = event.request.meeting.system_userids
        if system_userids:
            schema.add(colander.SchemaNode(colander.Set(),
                                           name = 'creator',
                                           title = _("Add as"),
                                           widget = add_as_system_user_widget,
                                           validator = current_user_or_system_users,
                                           preparer = to_tuple,
                                           default = current_userid_as_tuple,
                                           missing = current_userid_as_tuple))

def includeme(config):
    config.add_subscriber(system_users_in_add_schema, [DiscussionPostSchema, ISchemaCreatedEvent])
    config.add_subscriber(system_users_in_add_schema, [ProposalSchema, ISchemaCreatedEvent])
