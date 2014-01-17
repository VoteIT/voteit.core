import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from betahaus.pyracont.factories import createContent
from pyramid.traversal import find_interface

from zope.interface.interfaces import ComponentLookupError

from voteit.core.validators import html_string_validator
from voteit.core.validators import richtext_validator

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.schemas.tzdatetime import TZDateTime
from voteit.core.schemas.common import deferred_default_end_time
from voteit.core.schemas.common import deferred_default_start_time


@colander.deferred
def poll_plugin_choices_widget(node, kw):
    context = kw['context']
    request = kw['request']
    
    # get avaible plugins from the meeting
    meeting = find_interface(context, IMeeting)
    available_plugins = meeting.get_field_value('poll_plugins', ()) 
    
    #Add all selectable plugins to schema. This chooses the poll method to use
    plugin_choices = set()

    #FIXME: The new object should probably be sent to construct schema
    #for now, we can fake this
    fake_poll = createContent('Poll')

    # add avaible plugins the the choice set
    for name in available_plugins:
        #FIXME: we should probably catch if a plugin is no lnger avaible on the site 
        plugin = request.registry.getAdapter(fake_poll, name = name, interface = IPollPlugin) 
        plugin_choices.add((name, plugin.title))
        
    # if no plugins was set in the meetings add the default plugin if any is set 
    if not plugin_choices:
        name = request.registry.settings.get('default_poll_method', None)
        if name:
            plugin = request.registry.getAdapter(fake_poll, name = name, interface = IPollPlugin) 
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


@colander.deferred
def deferred_default_poll_method(node, kw):
    request = kw['request']
    return request.registry.settings.get('default_poll_method', '')


@schema_factory('AddPollSchema', title = _(u"Add poll"), description = _(u"Use this form to add a poll"))
@schema_factory('EditPollSchema', title = _(u"Edit poll"), description = _(u"Use this form to edit a poll"))
class PollSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(),
                                title = _(u"Title"),
                                validator=html_string_validator,)
    description = colander.SchemaNode(colander.String(),
                                      title = _(u"Description"),
                                      missing=u"",
                                      description = _(u"poll_description_description",
                                                      default=u"Explain your choice of poll method and your plan for the different polls in the agenda item."),
                                      widget=deform.widget.RichTextWidget(), 
                                      validator=richtext_validator,)

    poll_plugin = colander.SchemaNode(colander.String(),
                                      title = _(u"Poll method to use"),
                                      description = _(u"poll_poll_plugin_description",
                                                      default=u"Each poll method should have its own documentation. "
                                                        u"The standard ones from VoteITwill be in the manual - check the help menu!"),
                                      widget = poll_plugin_choices_widget,
                                      default = deferred_default_poll_method,)
                                      
    proposals = colander.SchemaNode(deform.Set(allow_empty=True), 
                                    name="proposals",
                                    title = _(u"Proposals"),
                                    description = _(u"poll_proposals_description",
                                                    default=u"Only proposals in the state 'published' can be selected"),
                                    missing=set(),
                                    widget=proposal_choices_widget,)
                                    
    add_reject_proposal = colander.SchemaNode(colander.Boolean(),
                                          title = _(u"Reject proposal"),
                                          description = _(u"add_reject_proposal_description",
                                                          default = u"Should a 'Reject all proposals' proposal be added to the poll?"),
                                          missing=False,
                                          widget=None)
                                          
    reject_proposal_title = colander.SchemaNode(colander.String(),
                                                title = _(u"Proposal text for 'reject all proposals'"),
                                                description = _(u"You can customise the proposal text if you want."),
                                                default = _(u"reject_proposal_title_default",
                                                            default = u"Reject all proposals"),
                                                widget = None)
    start_time = colander.SchemaNode(
         TZDateTime(),
         title = _(u"Start time of this poll."),
         description = _(u"You need to open it yourself."),
         widget=deform.widget.DateTimeInputWidget(options={'dateFormat': 'yy-mm-dd',
                                                           'timeFormat': 'hh:mm',
                                                           'separator': ' '}),
         default = deferred_default_start_time,
    )
    end_time = colander.SchemaNode(
         TZDateTime(),
         title = _(u"End time of this poll."),
         description = _(u"poll_end_time_description",
                         default = u"You need to close it yourself. A good default value is one day later."),
         widget=deform.widget.DateTimeInputWidget(options={'dateFormat': 'yy-mm-dd',
                                                           'timeFormat': 'hh:mm',
                                                           'separator': ' '}),
         default = deferred_default_end_time,
    )
    
def poll_schema_after_bind(node, kw):
    """ if a rejection proposal is already attatched to the poll
        those options should not be available """
    context = kw['context']
    if context.get_field_value('rejection_proposal_uid', None):
        del node['proposal_rejection']
        del node['proposal_rejection_title']
