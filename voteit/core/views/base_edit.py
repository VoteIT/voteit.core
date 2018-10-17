from __future__ import unicode_literals

from arche.exceptions import WorkflowException
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from voteit.core import _
from voteit.core.models.interfaces import IFlashMessages
from voteit.core.models.interfaces import IWorkflowAware


class ArcheFormCompat(object):
    #FIXME: Should be removed

    def appstruct(self):
        return self.context.get_field_appstruct(self.schema)

    def save_success(self, appstruct):
        self.flash_messages.add(self.default_success)
        self.context.set_field_appstruct(appstruct)
        return HTTPFound(location = self.request.resource_url(self.context))


@view_config(context=IWorkflowAware, name="state")
def state_change(context, request):
    """ Change workflow state for context.
        Note that permission checks are done by the workflow machinery.
        In case something goes wrong (for instance wrong permission) a
        WorkflowError will be raised.
    """
    state = request.params.get('state')
    try:
        context.workflow.do_transition(state, request)
    except WorkflowException as exc:
        raise HTTPForbidden(str(exc))
    fm = IFlashMessages(request)
    fm.add(_(context.workflow.state_title))
    if context.type_name == 'Poll': #Redirect to polls anchor
        url = request.resource_url(context.__parent__, anchor = context.uid)
    else:
        url = request.resource_url(context)
    return HTTPFound(location = url)
