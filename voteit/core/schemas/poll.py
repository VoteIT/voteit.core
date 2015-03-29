from arche.schemas import LocalDateTime
from pyramid.traversal import find_interface
import colander
import deform

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.interfaces import IProposal
from voteit.core.schemas.common import deferred_default_end_time
from voteit.core.schemas.common import deferred_default_start_time
from voteit.core.validators import html_string_validator
from voteit.core.validators import richtext_validator


@colander.deferred
def poll_plugin_choices_widget(node, kw):
    request = kw['request']
    values = []
    values.extend([(x.name, x.factory) for x in request.registry.registeredAdapters() if x.provided == IPollPlugin])
    return deform.widget.RadioChoiceWidget(values = values, template = "object_radio_choice")


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

@colander.deferred
def deferred_reject_proposal_title(node, kw):
    """ Translation strings as default values doesn't seem to work, so this method translates it. """
    request = kw['request']
    msg = _(u"reject_proposal_title_default", default = u"Reject all proposals")
    return request.localizer.translate(msg)


class PollSchema(colander.MappingSchema):
    
    title = colander.SchemaNode(colander.String(),
                                title = _(u"Title"),
                                validator = html_string_validator,)
    description = colander.SchemaNode(colander.String(),
                                      title = _(u"Description"),
                                      missing = u"",
                                      description = _(u"poll_description_description",
                                                      default=u"Explain your choice of poll method and your plan for the different polls in the agenda item."),
                                      widget=deform.widget.RichTextWidget(), 
                                      validator = richtext_validator,)
    poll_plugin = colander.SchemaNode(colander.String(),
                                      title = _(u"Poll method to use"),
                                      description = _(u"poll_poll_plugin_description",
                                                      default=u"Each poll method should have its own documentation. "
                                                        u"The standard ones from VoteITwill be in the manual - check the help menu!"),
                                      widget = poll_plugin_choices_widget,
                                      default = deferred_default_poll_method,)
                                      
    proposals = colander.SchemaNode(colander.Set(), 
                                    title = _(u"Proposals"),
                                    description = _(u"poll_proposals_description",
                                                    default=u"Only proposals in the state 'published' can be selected"),
                                    missing = set(),
                                    widget = proposal_choices_widget,)
    start_time = colander.SchemaNode(
         LocalDateTime(),
         title = _(u"Start time of this poll."),
         description = _(u"You need to open it yourself."),
         default = deferred_default_start_time,
         missing = colander.null,
    )
    end_time = colander.SchemaNode(
         LocalDateTime(),
         title = _(u"End time of this poll."),
         description = _(u"poll_end_time_description",
                         default = u"You need to close it yourself. A good default value is one day later."),
         default = deferred_default_end_time,
         missing = colander.null,
    )


class AddPollSchema(PollSchema):
    add_reject_proposal = colander.SchemaNode(colander.Boolean(),
                                          title = _(u"Reject proposal"),
                                          description = _(u"add_reject_proposal_description",
                                                          default = u"Should a 'Reject all proposals' proposal be added to the poll?"),
                                          missing=False)
    reject_proposal_title = colander.SchemaNode(colander.String(),
                                                title = _(u"Proposal text for 'reject all proposals'"),
                                                description = _(u"You can customise the proposal text if you want."),
                                                default = deferred_reject_proposal_title)


def includeme(config):
    config.add_content_schema('Poll', AddPollSchema, 'add')
    config.add_content_schema('Poll', PollSchema, 'edit')
