import colander
import deform
from zope.interface import implements
from zope.component import getUtilitiesFor

from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin


class Poll(BaseContent):
    """ Poll content. """
    implements(IPoll)
    
    content_type = 'Poll'
    omit_fields_on_edit = ['name']
    allowed_contexts = ['AgendaItem']


class PollSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())


def get_poll_schema():
    schema = PollSchema()

    choices = set()
    for (name, plugin) in getUtilitiesFor(IPollPlugin):
        choices.add((name, plugin.title))

    schema.add(colander.SchemaNode(colander.String(),
                                   name='poll_plugin',
                                   widget=deform.widget.SelectWidget(values=choices),),
               )

    return schema



