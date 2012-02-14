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

@schema_factory('LayoutSchema', title=_(u"Layout"), description=_(u"Change layout of meeting"))
class LayoutSchema(colander.Schema):
    meeting_left_widget = colander.SchemaNode(colander.String(),
                                              title = _(u"Meeting left column widget"),
                                              description = _(u"If no right column widget is selected, this will take up the whole page space."),
                                              widget = deferred_meeting_layout_left_widget,
                                              default = 'description_richtext',
                                              missing = colander.null,)
    meeting_right_widget = colander.SchemaNode(colander.String(),
                                               title = _(u"Meeting right column widget"),
                                               widget = deferred_meeting_layout_right_widget,
                                               missing = colander.null,)
    ai_left_widget = colander.SchemaNode(colander.String(),
                                         title = _(u"Agenda item left column widget"),
                                         description = _(u"If no right column widget is selected, this will take up the whole page space."),
                                         widget = deferred_ai_layout_left_widget,
                                         default = 'proposals',
                                         missing = colander.null,)
    ai_right_widget = colander.SchemaNode(colander.String(),
                                          title = _(u"Agenda item right column widget"),
                                          default = 'discussions',
                                          widget = deferred_ai_layout_right_widget,
                                          missing = colander.null,)
