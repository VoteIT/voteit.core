import colander

from voteit.core import _


class AgendaPortletSchema(colander.Schema):
    hide_type_count = colander.SchemaNode(
        colander.Bool(),
        title=_("Hide type and unread count"),
        description=_("Will speed up loading for physical meetings with lots of participants"),
        default=False,
        missing=False,
    )
