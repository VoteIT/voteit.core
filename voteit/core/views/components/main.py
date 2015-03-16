from betahaus.viewcomponent import view_action
from pyramid.renderers import render

from voteit.core import VoteITMF as _


@view_action('main', 'poll_state_info')
def render_poll_state_info(context, request, *args, **kwargs):
    response = dict(
        api = kwargs['api'],
        wf_state = context.get_workflow_state(),
        poll = context,
    )
    return render('../templates/snippets/poll_state_info.pt', response, request = request)


