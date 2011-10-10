from betahaus.pyracont.decorators import schema_factory
import colander
import deform

from voteit.core import VoteITMF as _
from voteit.core.validators import html_string_validator
from voteit.core.fields import TZDateTime


def start_time_node():
    return colander.SchemaNode(
        TZDateTime(),
        title = _('ai_start_time_title',
                  default=u"Estimated start time of this Agenda Item."),
        description = _(u"agenda_item_start_time_description",
                        default=u"This setting only sets the order for the agenda item's in the Agenda. You will still have to change the state of the agenda item manually with the gear beside it's name."),
        widget=deform.widget.DateTimeInputWidget(options={'timeFormat': 'hh:mm'}),
        missing = None,
    )


@schema_factory('AgendaItemSchema')
class AgendaItemSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(),
        title = _(u"Title"),
        description = _(u"Avoid a title with more than 20 characters"),
        validator=html_string_validator,
    )
    description = colander.SchemaNode(
        colander.String(),
        title = _(u"Description"),
        description = _(u"agenda_item_description_description",
                        default=u"Place the the agenda item background information here. You can link to external documents and memos. It's also a good idea to add an image, it will make it easier for participants to quickly see which page they're on."),
        missing = u"",
        widget=deform.widget.RichTextWidget(),
    )
    summary = colander.SchemaNode(
        colander.String(),
        title = _(u"Summary of this item."),
        description = _(u"agenda_item_summary_description",
                        default=u"This summary shows up to the right on the meetings first page. Write a short summary on what is going on or what has been decided. This should be updated as the meeting progresses."),
        #description = _('ai_summary_description',
        #                default=u"This could be what was decided. It will show up in the log on the meeting page."),
        widget=deform.widget.TextAreaWidget(rows=10, cols=60),
        missing = u"",
        validator=html_string_validator,
    )
    start_time = start_time_node()
    #End-time is handled by a subscriber when it is closed
