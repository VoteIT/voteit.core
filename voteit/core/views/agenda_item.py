from deform import Form
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.url import resource_url
from pyramid.security import has_permission
from zope.component.interfaces import ComponentLookupError
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from betahaus.pyracont.factories import createSchema

from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IVote
from voteit.core.models.schemas import add_csrf_token
from voteit.core.security import VIEW
from voteit.core.security import ADD_VOTE
from voteit.core.security import MODERATE_MEETING
from voteit.core.models.schemas import button_vote
from voteit.core.models.schemas import button_add
from voteit.core.fanstaticlib import voteit_deform
from voteit.core.fanstaticlib import autoresizable_textarea_js
from voteit.core.fanstaticlib import jquery_form
from voteit.core.fanstaticlib import star_rating


class AgendaItemView(BaseView):
    """ View for agenda items. """
    
    @view_config(context=IAgendaItem, renderer="templates/agenda_item.pt", permission=VIEW)
    def agenda_item_view(self):
        """ Main overview of Agenda item. """
        self.response['get_polls'] = self.get_polls
        self.response['polls'] = self.api.get_restricted_content(self.context, iface=IPoll, sort_on='created')
        for poll in self.response['polls']:
            try:
                plugin = poll.get_poll_plugin()
            except ComponentLookupError:
                err_msg = _(u"plugin_missing_error",
                            default = u"Can't find any poll plugin with name '${name}'. Perhaps that package has been uninstalled?",
                            mapping = {'name': poll.get_field_value('poll_plugin')})
                self.api.flash_messages.add(err_msg, type="error")
                continue

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
                                                                            
        # is needed because we load the forms with ajax
        voteit_deform.need()
        jquery_form.need()
        star_rating.need()
        
        # for autoexpanding textareas
        autoresizable_textarea_js.need()
        
        return self.response

    def get_polls(self, polls):
        response = {}
        response['api'] = self.api
        response['polls'] = polls
        return render('templates/polls.pt', response, request=self.request)
        
    @view_config(context=IAgendaItem, name='_inline_form', permission=VIEW)
    def inline_add_form(self):
        """ Inline add form. Note the somewhat odd permissions on the view configuration.
            The actual permission check for each content type is preformed later.
        """
        content_type = self.request.GET['content_type']
        add_permission = self.api.content_types_add_perm(content_type)
        if not has_permission(add_permission, self.context, self.request):
            raise HTTPForbidden("You're not allowed to add '%s' in this context." % content_type)
        
        schema_name = self.api.get_schema_name(content_type, 'add')
        schema = createSchema(schema_name).bind(context = self.context, request = self.request)
        add_csrf_token(self.context, self.request, schema)
        url = self.api.resource_url(self.context, self.request)
        form = Form(schema, action=url+"@@add?content_type="+content_type, buttons=(button_add,))
        #Note! Registration of form resources has to be in the view that has the javascript
        #that will include this!
        return Response(form.render())

    @view_config(context=IDiscussionPost, name="more", permission=VIEW, renderer='json')
    def discussion_more(self):
        return {'body': self.api.transform(self.context.get_field_value('title'))}
    
    @view_config(context=IAgendaItem, name="discussions", permission=VIEW)
    def discussions(self):
        if self.request.is_xhr:
            return Response(self.api.render_single_view_component(self.context, self.request, 'discussions', 'listing', api = self.api))
        
        if self.request.GET.get('discussions', None):
            url = resource_url(self.context, self.request, query={'discussions':'all'}, anchor="discussions")
        else:
            url = resource_url(self.context, self.request, anchor="discussions")
        return HTTPFound(location=url)

    @view_config(context = IAgendaItem, name = "_toggle_block", permission = MODERATE_MEETING)
    def toggle_block(self):
        """ Toggle wether discussion or proposals are allowed. """
        discussion_block = self.request.GET.get('discussion_block', None)
        proposal_block = self.request.GET.get('proposal_block', None)
        if discussion_block is not None:
            val = bool(int(discussion_block))
            self.context.set_field_value('discussion_block', val)
        if proposal_block is not None:
            val = bool(int(proposal_block))
            self.context.set_field_value('proposal_block', val)
        self.api.flash_messages.add(_(u"Status changed - note that workflow state also matters."))
        url = resource_url(self.context, self.request)
        return HTTPFound(location=url)
