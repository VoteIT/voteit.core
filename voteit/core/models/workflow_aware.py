from repoze.workflow import get_workflow
from repoze.workflow.workflow import WorkflowError
from zope.event import notify
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

    def initialize_workflow(self):
        #FIXME: the type should be som generic instead of the class name, but since the wrong workflow is returned this is is a workaround
        self.workflow.initialize(self)
        
    def get_workflow_state(self):
        return self.workflow.state_of(self)
        
    def set_workflow_state(self, request, state):
        """ Set a workflow state. """
        old_state = self.get_workflow_state()
        notify(WorkflowStateChange(self, old_state, state))
        
        self.workflow.transition_to_state(self, request, state)

    def make_workflow_transition(self, request, transition):
        """ Do a specific workflow transition. """
        old_state = self.get_workflow_state()
        self.workflow.transition(self, request, transition)
        new_state = self.get_workflow_state()
        notify(WorkflowStateChange(self, old_state, new_state))
            
    def get_available_workflow_states(self, request):
        states = self.workflow.state_info(self, request)
        astates = []
        for state in states:
            if state['transitions']:
                astates.append(state)
        return astates
