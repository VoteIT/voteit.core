from deform import Form
from pyramid.renderers import render
from pyramid.view import view_config
from pyramid.url import resource_url
from pyramid.security import has_permission
from pyramid.renderers import render_to_response
from zope.component.interfaces import ComponentLookupError
from betahaus.pyracont.factories import createSchema

from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IVote
from voteit.core.security import VIEW
from voteit.core.security import ADD_VOTE
from voteit.core.models.schemas import button_vote
from voteit.core.models.schemas import button_add


class AgendaItemView(BaseView):
    """ View for agenda items. """
    
    @view_config(context=IAgendaItem, renderer="templates/agenda_item.pt", permission=VIEW)
    def agenda_item_view(self):
        """ Main overview of Agenda item. """
        self.response['get_polls'] = self.get_polls
        self.response['polls'] = self.api.get_restricted_content(self.context, iface=IPoll, sort_on='created')        
        poll_forms = {}
        for poll in self.response['polls']:
            #Check if the users vote exists already
            userid = self.api.userid
            try:
                plugin = poll.get_poll_plugin()
            except ComponentLookupError:
                err_msg = _(u"plugin_missing_error",
                            default = u"Can't find any poll plugin with name '${name}'. Perhaps that package has been uninstalled?",
                            mapping = {'name': poll.get_field_value('poll_plugin')})
                self.api.flash_messages.add(err_msg, type="error")
                poll_forms[poll.uid] = ''
                continue
            poll_schema = plugin.get_vote_schema()
            appstruct = {}
            can_vote = has_permission(ADD_VOTE, poll, self.request)

            if can_vote:
                poll_url = resource_url(poll, self.request)
                form = Form(poll_schema, action=poll_url+"@@vote", buttons=(button_vote,), formid=poll.__name__)
            else:
                form = Form(poll_schema, formid=poll.__name__)
            self.api.register_form_resources(form)

            if userid in poll:
                #If editing a vote is allowed, redirect. Editing is only allowed in open polls
                vote = poll.get(userid)
                assert IVote.providedBy(vote)
                #show the users vote and edit button
                appstruct = vote.get_vote_data()
                #Poll might still be open, in that case the poll should be changable
                readonly = not can_vote
                poll_forms[poll.uid] = form.render(appstruct=appstruct, readonly=readonly)
            #User has not voted
            elif can_vote:
                poll_forms[poll.uid] = form.render()
        self.response['poll_forms'] = poll_forms
        _marker = object()
        rwidget = self.api.meeting.get_field_value('ai_right_widget', _marker)
        if rwidget is _marker:
            rwidget = 'discussions'
        
        colkwargs = dict(group_name = 'ai_widgets',
                         col_one = self.api.meeting.get_field_value('ai_left_widget', 'proposals'),
                         col_two = rwidget,
                         )
        self.response['ai_columns'] = self.api.render_single_view_component(self.context, self.request,
                                                                            'main', 'columns',
                                                                            **colkwargs)
        return self.response

    def get_polls(self, polls, poll_forms):
        response = {}
        response['api'] = self.api
        response['polls'] = polls
        response['poll_forms'] = poll_forms
        return render('templates/polls.pt', response, request=self.request)


    @view_config(context=IAgendaItem, name="discussions", permission=VIEW, renderer='templates/discussions.pt')
    def meeting_messages(self):
        self.response['discussions'] = self.context.get_content(iface=IDiscussionPost, sort_on='created')
        return self.response
        
    @view_config(context=IAgendaItem, name='inline_form', permission=VIEW)
    def inline_add_form(self):
        content_type = self.request.GET['content_type']
        
        add_permission = self.api.content_types_add_perm(content_type)
        if not has_permission(add_permission, self.context, self.request):
            raise Forbidden("You're not allowed to add '%s' in this context." % content_type)
        
        schema_name = self.api.get_schema_name(content_type, 'add')
        schema = createSchema(schema_name).bind(context = self.context, request = self.request)
        url = self.api.resource_url(self.context, self.request)
        form = Form(schema, action=url+"@@add?content_type="+content_type, buttons=(button_add,))
        self.api.register_form_resources(form)
        
        response = {}
        response['form'] = form.render()
        response['api'] = self.api
        
        return render_to_response('templates/snippets/inline_add_form.pt', response, request = self.request)
