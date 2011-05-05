import colander
import deform
from zope.interface import implements
from zope.component import getUtilitiesFor
from pyramid.traversal import find_interface

from voteit.core.models.agenda_item import AgendaItem
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
    
    
def update_poll_schema(schema, context):
    """ Wrapper to allow fields to be added when we have a context.
    """
    #Poll method, Ie which poll plugin to use
    plugin_choices = set()
    for (name, plugin) in getUtilitiesFor(IPollPlugin):
        plugin_choices.add((name, plugin.title))

    schema.add(colander.SchemaNode(colander.String(),
                                 name='poll_plugin',
                                 widget=deform.widget.SelectWidget(values=plugin_choices),),)
    
    #Proposals to vote on
    proposal_choices = set()
    agenda_item = find_interface(context, AgendaItem)
    [proposal_choices.add((x.uid, x.title)) for x in agenda_item.values() if x.content_type == 'Proposal']

    schema.add(colander.SchemaNode(deform.Set(),
                                 name="proposals",
                                 widget=deform.widget.CheckboxChoiceWidget(values=proposal_choices),),)
