from deform import Form
from betahaus.pyracont.factories import createSchema
from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from zope.interface.interfaces import ComponentLookupError

from voteit.core.models.schemas import button_login
from voteit.core import VoteITMF as _
from voteit.core.helpers import strip_and_truncate


def _show_login(api):
    if api.userid:
        return False
    url = api.request.path_url
    if url.endswith('login') or url.endswith('register'):
        return False
    return True


@view_action('sidebar', 'login_pw')
def login_box(context, request, va, **kwargs):
    api = kwargs['api']
    if not _show_login(api):
        return u""
    #FIXME: Ticket system makes it a bit of a hassle to make login detached from registration.
    #We'll do that later. For now, let's just check if user is on login or registration page
    login_schema = createSchema('LoginSchema').bind(context = context, request = request)
    action_url = request.resource_url(api.root, 'login')
    login_form = Form(login_schema, buttons=(button_login,), action=action_url)
    api.register_form_resources(login_form)
    response = dict(
        api = api,
        form = login_form.render(),
    )
    return render('templates/sidebars/login_pw.pt', response, request = request)

@view_action('sidebar', 'login_alt')
def alternative_login_methods(context, request, va, **kwargs):
    api = kwargs['api']
    if not _show_login(api):
        return u""
    try:
        return """<div class="sidebar_block" id="login_alt">%s</div>""" % \
            api.render_view_group(api.root, request, 'login_forms', **kwargs)
    except ComponentLookupError: #There's no login_forms view group
        return u""

@view_action('sidebar', 'moderator_agenda_actions')
def moderator_agenda_actions(context, request, va, **kwargs):
    api = kwargs['api']
    if not api.show_moderator_actions:
        return u""
    if api.meeting: #meeting context
        return api.get_moderator_actions(api.meeting)
    else: #root context
        return api.get_moderator_actions(api.root)


@view_action('sidebar', 'latest_meeting_entries')
def latest_meeting_entries(context, request, va, **kwargs):
    #FIXME: This is disabled for now, needs proper design
    return ''
    api = kwargs['api']
    
    # only avaible in meeting
    if not api.meeting:
        return ''
    
    response = dict(
        api = api,
        context = context,
        truncate = strip_and_truncate,
        closed_section = False,
    )
    
    if request.cookies.get('latest_meeting_entries'):
        response['closed_section'] = True
        return render('../templates/snippets/latest_meeting_entries.pt', response, request = request)
    
    response['closed_section'] = False
    
    query = {}
    query['path'] = resource_path(api.meeting)
    query['allowed_to_view'] = {'operator':'or', 'query': effective_principals(request)}
    query['content_type'] = {'query':('Proposal','DiscussionPost'), 'operator':'or'}
    query['sort_index'] = 'created'
    query['reverse'] = True
    query['limit'] = 5
    
    response['last_entries'] = api.get_metadata_for_query(**query)
    
    return render('../templates/snippets/latest_meeting_entries.pt', response, request = request)
