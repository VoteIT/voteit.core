from betahaus.viewcomponent import view_action

from voteit.core import VoteITMF as _


@view_action('meeting_widgets', 'description_richtext', title = _(u"Description richtext field (default left column)"))
def description_richtext(context, request, va, **kw):
    return """<div class="description">%s</div>""" % context.description
