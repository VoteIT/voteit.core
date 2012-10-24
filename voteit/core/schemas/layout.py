import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from betahaus.viewcomponent.interfaces import IViewGroup

from voteit.core import VoteITMF as _


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
def deferred_meeting_layout_left_widget(node, kw):
    request = kw['request']
    choices = _get_choices(request, 'meeting_widgets')
    return deform.widget.RadioChoiceWidget(values=choices)

@colander.deferred
def deferred_meeting_layout_right_widget(node, kw):
    request = kw['request']
    choices = _get_choices(request, 'meeting_widgets')
    choices.append(('', _(u"<Disable>")))
    return deform.widget.RadioChoiceWidget(values=choices)

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

@schema_factory('LayoutSchema', title=_(u"Layout"),
                description=_(u"layuot_schema_main_description",
                              default = u"Change layout of the different parts in the meeting (advanced feature)"))
class LayoutSchema(colander.Schema):
    meeting_left_widget = colander.SchemaNode(colander.String(),
                                              title = _(u"Meeting left column widget"),
                                              description = _(u"meeting_left_widget_description",
                                                              default = u"If no right column widget is selected, this will take up the whole page space."),
                                              widget = deferred_meeting_layout_left_widget,
                                              default = 'description_richtext',
                                              missing = u"",)
    meeting_right_widget = colander.SchemaNode(colander.String(),
                                               title = _(u"Meeting right column widget"),
                                               widget = deferred_meeting_layout_right_widget,
                                               missing = u"",)
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
                                                          default = u"Set the number of always visible characters in discussion posts. Enter 0 for no truncating."),
                                          default = 240,
                                          widget = deform.widget.TextInputWidget(),
                                          missing = 240,
                                          validator=colander.Range(0),)
    tags_enabled = colander.SchemaNode(colander.Boolean(),
                                      title = _(u"Enable tags"),
                                      description = _(u"enable_tags_description",
                                                      default = u"Enable tags in proposals and discussion posts"),
                                      default = True,
                                      widget = deform.widget.CheckboxWidget(),
                                      missing = True,)
    show_retracted = colander.SchemaNode(colander.Boolean(),
                               title = _(u"Show retracted"),
                               description = _(u"meeting_show_retracted_description",
                                               default=u"Always show retracted proposals."),
                               default = True,)