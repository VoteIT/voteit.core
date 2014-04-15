import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from betahaus.viewcomponent.interfaces import IViewGroup

from voteit.core import VoteITMF as _
from voteit.core.schemas.interfaces import ILayoutSchema

def _get_choices(request, group_name):
    util = request.registry.queryUtility(IViewGroup, name = group_name)
    choices = []
    if util is not None:
        for (name, va) in util.items():
            title = va.title and va.title or name
            item = (name, title)
            choices.append(item)
    return choices

@colander.deferred
def deferred_ai_layout_left_widget(node, kw):
    request = kw['request']
    choices = _get_choices(request, 'ai_widgets')
    return deform.widget.RadioChoiceWidget(values=choices)

@colander.deferred
def deferred_ai_layout_right_widget(node, kw):
    request = kw['request']
    choices = _get_choices(request, 'ai_widgets')
    choices.append(('', _(u"<Disable>")))
    return deform.widget.RadioChoiceWidget(values=choices)


#Provides for schemas is to be considered experimental!
@schema_factory(title=_(u"Layout"),
                description=_(u"layuot_schema_main_description",
                              default = u"Change layout of the different parts in the meeting (advanced feature)"),
                provides = ILayoutSchema)
class LayoutSchema(colander.Schema):
    meeting_logo_url = colander.SchemaNode(colander.String(),
                                           title = _(u"URL to a meeting logo."),
                                           description = _(u"logo_description_text",
                                                           default = u"It will be shown to the left of the header. "
                                                           u"Dimensions should be no more than the text height. "
                                                           u"If you use the wrong dimensions, you may break the layout."),
                                           missing = u"")
    ai_left_widget = colander.SchemaNode(colander.String(),
                                         title = _(u"Agenda item left column widget"),
                                         widget = deferred_ai_layout_left_widget,
                                         default = 'proposals',
                                         missing = u"",)
    ai_right_widget = colander.SchemaNode(colander.String(),
                                          title = _(u"Agenda item right column widget"),
                                          default = 'discussions',
                                          widget = deferred_ai_layout_right_widget,
                                          missing = u"",)
    truncate_discussion_length = colander.SchemaNode(colander.Integer(),
                                          title = _(u"Truncate discussion length"),
                                          description = _(u"truncate_discussion_length_description",
                                                          default = u"Set the number of always visible characters "
                                                            u"in discussion posts. Enter 0 for no truncating."),
                                          default = 240,
                                          widget = deform.widget.TextInputWidget(),
                                          missing = 240,
                                          validator=colander.Range(0),)
    hide_retracted = colander.SchemaNode(colander.Boolean(),
                                   title = _(u"Hide retracted proposals"),
                                   description = _(u"meeting_hide_retracted_description",
                                                   default=u"You can still access hidden proposals "
                                                      u"by using a collapsible link below the regular proposals."),)
    hide_unhandled_proposals = colander.SchemaNode(colander.Boolean(),
        title = _(u"Hide unhandled proposals"),
        description = _(u"meeting_hide_unhandled_description",
                        default=u"In the same fashion as retracted proposals."),
        default = True,
        missing = True)
