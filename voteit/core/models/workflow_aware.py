from repoze.workflow import get_workflow
from repoze.workflow.workflow import WorkflowError
from zope.component.event import objectEventNotify
from zope.interface import implements

from voteit.core.models.interfaces import IWorkflowAware
from voteit.core.events import WorkflowStateChange


class WorkflowAware(object):
    """ Mixin class to make content workflow-aware. See IWorkflowAware """
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
        """ Set a workflow state. """
        old_state = self.get_workflow_state()        
        self.workflow.transition_to_state(self, request, state)
        objectEventNotify(WorkflowStateChange(self, old_state, state))

    def make_workflow_transition(self, request, transition):
        """ Do a specific workflow transition. """
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
        """ Return (untranslated) state title for the current state. """
        for info in self.workflow.state_info(self, request):
            if info['current']:
                return info['title']
        raise WorkflowError("No workflow title found on object: %s" % self)
