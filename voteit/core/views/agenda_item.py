from deform import Form
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.traversal import resource_path
from pyramid.security import has_permission
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from betahaus.pyracont.factories import createSchema
from pyramid.traversal import find_interface
from deform.exception import ValidationFailure

from voteit.core import VoteITMF as _
from voteit.core.helpers import ajax_options
from voteit.core.helpers import generate_slug
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IProposal
from voteit.core.models.schemas import button_add
from voteit.core.security import MODERATE_MEETING
from voteit.core.security import VIEW
from voteit.core.views.base_view import BaseView


def inline_add_form(api, content_type, bind_data):
    """ Expects the context for the add form to be the current requests context.
        This is only used within the agenda item view currently.
    """
    tag = api.request.GET.get('tag', '')
    schema_name = api.get_schema_name(content_type, 'add')
    schema = createSchema(schema_name, bind = bind_data)
    query = {'content_type': content_type, 'tag': tag}
    url = api.request.resource_url(api.context, '_inline_form', query = query)
    return Form(schema, action = url, buttons = (button_add,), use_ajax = True)


class AgendaItemView(BaseView):
    """ View for agenda items. """
    
#    @view_config(context=IAgendaItem, renderer="templates/agenda_item.pt", permission=VIEW)
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
        self.response['next_ai'] = self.next_ai()
        self.response['previous_ai'] = self.previous_ai()
        if self.request.is_xhr:
            Response(render('templates/ajax_tag_filter.pt', self.response, request=self.request))
        return self.response

    def next_ai(self):
        """ Return next qgenda item within this workflow category, if there is one.
        """
        query = u"path == '%s' and content_type == 'AgendaItem'" % resource_path(self.context.__parent__)
        query += u" and order > %s" % self.context.get_field_value('order')
        query += u" and workflow_state == '%s'" % self.context.get_workflow_state()
        #Note that docids might be a generator here
        count, docids = self.api.query_catalog(query , limit = 1, sort_index='order')
        if not count:
            return
        return self.api.resolve_catalog_docid(tuple(docids)[0])

    def previous_ai(self):
        """ Return previous agenda item within this workflow category, if there is one.
        """
        query = u"path == '%s' and content_type == 'AgendaItem'" % resource_path(self.context.__parent__)
        query += u" and order < %s" % self.context.get_field_value('order')
        query += u" and workflow_state == '%s'" % self.context.get_workflow_state()
        #Note that docids might be a generator here
        count, docids = self.api.query_catalog(query , limit = 1, sort_index='order', reverse = True)
        if not count:
            return
        return self.api.resolve_catalog_docid(tuple(docids)[0])

 #   @view_config(context=IAgendaItem, name='_inline_form', permission=VIEW)
    def process_inline_add_form(self):
        """ Inline add form. Note the somewhat odd permissions on the view configuration.
            The actual permission check for each content type is preformed later.
        """
        content_type = self.request.GET['content_type']
        add_permission = self.api.content_types_add_perm(content_type)
        if not has_permission(add_permission, self.context, self.request):
            raise HTTPForbidden("You're not allowed to add '%s' in this context." % content_type)
        bind_data = dict(context = self.context, request = self.request, api = self.api)
        form = inline_add_form(self.api, content_type, bind_data)
        post = self.request.POST
        if 'add' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                msg = self.api.translate(_(u"There were errors so your post hasn't been submitted yet."))
                html = u"""
                <script type="text/javascript">
                    flash_message("%s", 'error', true, 3, true);
                </script>
                """ % msg
                html += e.render()
                return Response(html)
            kwargs = {}
            kwargs.update(appstruct)
            if self.api.userid:
                kwargs['creators'] = [self.api.userid]
            obj = createContent(content_type, **kwargs)
            name = generate_slug(self.context, obj.title)
            self.context[name] = obj
            #Prep js response
            tag = self.request.GET.get('tag', '')
            url = self.request.resource_url(self.context, query = {'tag': tag})
            if content_type == 'Proposal':
                area = 'proposals'
            else:
                area = 'discussions'
            txt = self.api.translate(_(u"Posting..."))
            response = '<div><img src="/static/images/spinner.gif" />%s</div>' % txt
            response += '<script type="text/javascript">'
            response += "reload_ai_listings('%s', ['%s']);" % (url, area)
            response += "mark_as_read();"
            response += '</script>'
            return Response(response)
        #Note! Registration of form resources has to be in the view that has the javascript
        #that will include this!
        self.response['form'] = form.render()
        self.response['user_image_tag'] = self.api.user_profile.get_image_tag(request = self.request)
        self.response['content_type'] = content_type
        return Response(render('templates/snippets/inline_form.pt', self.response, request=self.request))

 #   @view_config(context=IDiscussionPost, name="more", permission=VIEW, renderer='json')
    def discussion_more(self):
        return {'body': self.api.transform(self.context.get_field_value('title'))}
    
  #  @view_config(context=IAgendaItem, name="discussions", permission=VIEW)
    def discussions(self):
        if self.request.is_xhr:
            return Response(self.api.render_single_view_component(self.context, self.request, 'discussions', 'listing', api = self.api))
        
        url = self.request.resource_url(self.context, query=self.request.GET, anchor="discussions")
        return HTTPFound(location=url)

 #   @view_config(context = IAgendaItem, name = "_toggle_block", permission = MODERATE_MEETING)
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
        url = self.request.resource_url(self.context)
        if self.request.referer:
            url = self.request.referer
        return HTTPFound(location=url)

   # @view_config(context=IDiscussionPost, name="answer", permission=VIEW, renderer='templates/base_edit.pt')
   # @view_config(context=IProposal, name="answer", permission=VIEW, renderer='templates/base_edit.pt')
    def discussion_answer(self):
        content_type = 'DiscussionPost'
        ai = find_interface(self.context, IAgendaItem)
        add_permission = self.api.content_types_add_perm(content_type)
        if not has_permission(add_permission, ai, self.request):
            raise HTTPForbidden("You're not allowed to add '%s' in this context." % content_type)
        
        schema_name = self.api.get_schema_name(content_type, 'add')
        schema = createSchema(schema_name).bind(context = self.context, request = self.request, api = self.api)
        
        url = self.request.resource_url(self.context, 'answer')
        form = Form(schema, 
                    action=url, 
                    buttons=(button_add,),
                    formid="answer-form-%s" % self.context.uid, 
                    use_ajax=False,
                    ajax_options=ajax_options)
        self.api.register_form_resources(form)
        
        self.response['user_image_tag'] = self.api.user_profile.get_image_tag(request = self.request)
        self.response['content_type'] = content_type
        
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

            #Success, redirect
            url = self.request.resource_url(ai, anchor=obj.uid)
            if self.request.is_xhr:
                return Response(headers = [('X-Relocate', url)])
            return HTTPFound(location=url)
        
        self.response['form'] = form.render()
        
        if self.request.is_xhr:
            return Response(render('templates/snippets/inline_form.pt', self.response, request=self.request))
        return self.response
