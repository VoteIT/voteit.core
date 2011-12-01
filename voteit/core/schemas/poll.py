import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from betahaus.pyracont.factories import createContent
from pyramid.traversal import find_interface

from voteit.core.validators import html_string_validator
from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.schemas.tzdatetime import TZDateTime
from voteit.core.schemas.common import deferred_default_end_time
from voteit.core.schemas.common import deferred_default_start_time


@colander.deferred
def poll_plugin_choices_widget(node, kw):
    request = kw['request']
    
    #Add all selectable plugins to schema. This chooses the poll method to use
    plugin_choices = set()

    #FIXME: The new object should probably be sent to construct schema
    #for now, we can fake this
    fake_poll = createContent('Poll')

    for (name, plugin) in request.registry.getAdapters([fake_poll], IPollPlugin):
        plugin_choices.add((name, plugin.title))

    return deform.widget.SelectWidget(values=plugin_choices)


@colander.deferred
def proposal_choices_widget(node, kw):
    context = kw['context']
    #Proposals to vote on
    proposal_choices = set()
    agenda_item = find_interface(context, IAgendaItem)
    if agenda_item is None:
        Exception("Couldn't find the agenda item from this polls context")
        
    #Get valid proposals - should be in states 'published' to be selectable
    for prop in agenda_item.get_content(iface=IProposal, states='published', sort_on='title'):
        proposal_choices.add((prop.uid, prop.title, ))

    # get currently chosen proposals
    if IPoll.providedBy(context):
        for prop in context.get_proposal_objects():
            proposal_choices.add((prop.uid, prop.title, ))

    proposal_choices = sorted(proposal_choices, key=lambda proposal: proposal[1].lower())
    return deform.widget.CheckboxChoiceWidget(values=proposal_choices)


@schema_factory('PollSchema')
class PollSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(),
                                title = _(u"Title"),
                                validator=html_string_validator,)
    description = colander.SchemaNode(colander.String(),
                                      title = _(u"Description"),
                                      missing=u"",
                                      description = _(u"poll_description_description",
                                                      default=u"Explain your choice of poll method and your plan for the different polls in the agenda item."),
                                      widget=deform.widget.RichTextWidget(),)

    poll_plugin = colander.SchemaNode(colander.String(),
                                      title = _(u"Poll method to use"),
                                      description = _(u"poll_poll_plugin_description",
                                                      default=u"Read in the help wiki about pros and cons of different polling methods."),
                                      widget=poll_plugin_choices_widget,)
                                      
    proposals = colander.SchemaNode(deform.Set(allow_empty=True), 
                                    name="proposals",
                                    title = _(u"Proposals"),
                                    description = _(u"poll_proposals_description",
                                                    default=u"Only proposals in the state 'published' can be selected"),
                                    missing=set(),
                                    widget=proposal_choices_widget,)
                                    
    proposal_rejection = colander.SchemaNode(colander.Boolean(),
                                          name="proposal_rejection",
                                          title = _(u"Rejection proposal"),
                                          description = _(u"Should a rejection proposal be added to the poll"),
                                          missing=False,
                                          widget=None)
                                          
    proposal_rejection_title = colander.SchemaNode(colander.String(),
                                                name="proposal_rejection_title",
                                                title = _(u"Rejection proposal title"),
                                                description = _(u"The title of the rejection proposal"),
                                                default=_("Rejection"),
                                                widget=None)
    start_time = colander.SchemaNode(
         TZDateTime(),
         title = _(u"Start time of this poll."),
         description = _(u"You need to open it yourself."),
         widget=deform.widget.DateTimeInputWidget(options={'timeFormat': 'hh:mm'}),
         default = deferred_default_start_time,
    )
    end_time = colander.SchemaNode(
         TZDateTime(),
         title = _(u"End time of this poll."),
         description = _(u"poll_end_time_description",
                         default = u"You need to close it yourself. A good default value is one day later."),
         widget=deform.widget.DateTimeInputWidget(options={'timeFormat': 'hh:mm'}),
         default = deferred_default_end_time,
    )
    
def poll_schema_after_bind(node, kw):
    """ if a rejection proposal is already attatched to the poll
        those options should not be available """
    context = kw['context']
    if context.get_field_value('rejection_proposal_uid', None):
        del node['proposal_rejection']
        del node['proposal_rejection_title']
