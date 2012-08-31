from deform import Form
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.url import resource_url
from pyramid.security import has_permission
from zope.component.interfaces import ComponentLookupError
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from betahaus.pyracont.factories import createContent
from betahaus.pyracont.factories import createSchema
from pyramid.traversal import find_interface
from deform.exception import ValidationFailure

from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IProposal
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
from voteit.core.fanstaticlib import jquery_caret
from voteit.core.helpers import generate_slug
from voteit.core.helpers import ajax_options


class AgendaItemView(BaseView):
    """ View for agenda items. """
    
    @view_config(context=IAgendaItem, renderer="templates/agenda_item.pt", permission=VIEW)
    def agenda_item_view(self):
        """ Main overview of Agenda item. """

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
        jquery_caret.need()
        
        # for autoexpanding textareas
        autoresizable_textarea_js.need()
        
        if self.request.is_xhr:
            Response(render('templates/ajax_tag_filter.pt', self.response, request=self.request))
        return self.response
        
    @view_config(context=IAgendaItem, name='_inline_form', permission=VIEW)
    def inline_add_form(self):
        """ Inline add form. Note the somewhat odd permissions on the view configuration.
            The actual permission check for each content type is preformed later.
        """
        content_type = self.request.GET['content_type']
        tag = self.request.GET.get('tag', '')
        add_permission = self.api.content_types_add_perm(content_type)
        if not has_permission(add_permission, self.context, self.request):
            raise HTTPForbidden("You're not allowed to add '%s' in this context." % content_type)
        
        schema_name = self.api.get_schema_name(content_type, 'add')
        schema = createSchema(schema_name).bind(context = self.context, request = self.request)
        add_csrf_token(self.context, self.request, schema)
        query = {'content_type': content_type,
                 'tag': tag}
        url = self.request.resource_url(self.context, '@@add', query=query)
        form = Form(schema, action=url, buttons=(button_add,))
        #Note! Registration of form resources has to be in the view that has the javascript
        #that will include this!
        appstruct={'tags': tag}
        if tag:
            if content_type == 'Proposal':
                appstruct['title'] = " #%s" % tag
            else:
                appstruct['text'] = " #%s" % tag 
        else:
           if content_type == 'Proposal':
                appstruct['title'] = "%s " % _('I propose')
        self.response['form'] = form.render(appstruct=appstruct)
        self.response['user_image_tag'] = self.api.user_profile.get_image_tag()
        return Response(render('templates/snippets/inline_form.pt', self.response, request=self.request))

    @view_config(context=IDiscussionPost, name="more", permission=VIEW, renderer='json')
    def discussion_more(self):
        return {'body': self.api.transform(self.context.get_field_value('title'))}
    
    @view_config(context=IAgendaItem, name="discussions", permission=VIEW)
    def discussions(self):
        if self.request.is_xhr:
            return Response(self.api.render_single_view_component(self.context, self.request, 'discussions', 'listing', api = self.api))
        
        url = resource_url(self.context, self.request, query=self.request.GET, anchor="discussions")
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

    @view_config(context=IDiscussionPost, name="answer", permission=VIEW, renderer='templates/base_edit.pt')
    @view_config(context=IProposal, name="answer", permission=VIEW, renderer='templates/base_edit.pt')
    def discussion_answer(self):
        content_type = 'DiscussionPost'
        ai = find_interface(self.context, IAgendaItem)
        add_permission = self.api.content_types_add_perm(content_type)
        if not has_permission(add_permission, ai, self.request):
            raise HTTPForbidden("You're not allowed to add '%s' in this context." % content_type)
        
        schema_name = self.api.get_schema_name(content_type, 'add')
        schema = createSchema(schema_name).bind(context = self.context, request = self.request)
        add_csrf_token(self.context, self.request, schema)
        
        url = self.api.resource_url(self.context, self.request)
        form = Form(schema, 
                    action=url+"@@answer", 
                    buttons=(button_add,),
                    formid="answer-form-%s" % self.context.uid, 
                    use_ajax=True,
                    ajax_options=ajax_options)
        self.api.register_form_resources(form)
        
        post = self.request.POST
        if 'add' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                if self.request.is_xhr:
                    return Response(render("templates/ajax_edit.pt", self.response, request = self.request))
                return self.response
            
            kwargs = {}
            kwargs['text'] = appstruct['text']
            if self.api.userid:
                kwargs['creators'] = [self.api.userid]

            ai = find_interface(self.context, IAgendaItem)
            
            obj = createContent(content_type, **kwargs)
            name = generate_slug(ai, obj.title)
            ai[name] = obj
            # add the tags
            obj.add_tags(appstruct['tags'])

            #Success, redirect
            url = self.request.resource_url(ai, anchor=obj.uid)
            if self.request.is_xhr:
                return Response(headers = [('X-Relocate', url)])
            return HTTPFound(location=url)
        
        # get creator of answered object
        creators = self.context.get_field_value('creators')
        if creators:
            creator = "@%s" % creators[0]
        else:
            creator = ''
            
        # get tags and make a string of them
        tags = []
        for tag in self.context._tags:
            tags.append("#%s" % tag)
        
        appstruct = {'tags': " ".join(self.context._tags),
                     'text': "%s:  %s" % (creator, " ".join(tags))}
        
        self.response['form'] = form.render(appstruct=appstruct)
        
        if self.request.is_xhr:
            return Response(render('templates/ajax_edit.pt', self.response, request=self.request))
        return self.response
