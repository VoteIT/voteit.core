import warnings

from arche.exceptions import WorkflowException
from arche.interfaces import IWorkflowAfterTransition
from repoze.workflow import get_workflow
from repoze.workflow.workflow import WorkflowError
from zope.component.event import objectEventNotify
from zope.interface import implements, implementer

from voteit.core.models.interfaces import IWorkflowAware
from voteit.core.events import WorkflowStateChange


class WorkflowAware(object):
    """ Mixin class to make content workflow-aware.
        See :mod:`voteit.core.models.interfaces.IWorkflowAware`.
    """
    implements(IWorkflowAware)

    @property
    def workflow(self):
        try:
            self.content_type
        except AttributeError:
            raise WorkflowError("context doesn't have content_type attribute set")

        for iface in self.__class__.__implemented__.interfaces():
            wf = get_workflow(iface, self.content_type, self)
            if wf is not None:
                return wf
        raise WorkflowError("Workflow not found for %s" % self)
        
    def get_workflow_state(self):
        return self.workflow.state_of(self)
        
    def set_workflow_state(self, request, state):
        old_state = self.get_workflow_state()        
        self.workflow.transition_to_state(self, request, state)
        objectEventNotify(WorkflowStateChange(self, old_state, state))

    def make_workflow_transition(self, request, transition):
        old_state = self.get_workflow_state()
        self.workflow.transition(self, request, transition)
        new_state = self.get_workflow_state()
        objectEventNotify(WorkflowStateChange(self, old_state, new_state))
            
    def get_available_workflow_states(self, request):
        states = self.workflow.state_info(self, request)
        astates = []
        for state in states:
            if state['transitions']:
                astates.append(state)
        return astates

    def current_state_title(self, request):
        for info in self.workflow.state_info(self, request):
            if info['current']:
                return info['title']
        raise WorkflowError("No workflow title found on object: %s" % self)


@implementer(IWorkflowAware)
class WorkflowCompatMixin(object):
    """ Mixin class to make content implement parts of VoteiTs old workflow system.
        See :mod:`voteit.core.models.interfaces.IWorkflowAware`.
    """
    # workflow prop is the same

    def get_workflow_state(self):
        warnings.warn("get_workflow_state is deprecated, use wf_state instead", DeprecationWarning)
        return self.wf_state

    def set_workflow_state(self, request, state):
        warnings.warn("set_workflow_state is deprecated, use workflow.do_transition() instead", DeprecationWarning)
        if self.workflow:
            return self.workflow.do_transition(state, request=request)
        raise WorkflowException("Workflow not configured for '%s'" % self)

    def make_workflow_transition(self, request, transition):
        raise Exception('Not used?')

    def get_available_workflow_states(self, request):
        warnings.warn("get_available_workflow_states is deprecated, use workflow.get_transitions() instead", DeprecationWarning)
        return list(self.workflow.get_transitions(request))

    def current_state_title(self, request):
        warnings.warn("get_available_workflow_states is deprecated, use workflow.state_title instead", DeprecationWarning)
        return self.workflow.state_title


def compat_event(context, event):
    deprecated_event = WorkflowStateChange(context, old_state=event.from_state, new_state=event.to_state)
    objectEventNotify(deprecated_event)


def includeme(config):
    # Compat - tie WorkflowStateChange
    config.add_subscriber(compat_event, [IWorkflowAware, IWorkflowAfterTransition])