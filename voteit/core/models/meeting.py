import colander

from pyramid.security import Allow
from voteit.core.models.base_content import BaseContent
from voteit.core import security


class Meeting(BaseContent):
    """ Meeting content. """
    content_type = 'Meeting'
    omit_fields_on_edit = ('name',)
    allowed_contexts = ('SiteRoot',)
    add_permission = security.ADD_MEETING

    __acl__ = [(Allow, security.ROLE_MODERATOR, security.ALL_ADD_PERMISSIONS),
               ]


class MeetingSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())
