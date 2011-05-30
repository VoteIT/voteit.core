from repoze.workflow import get_workflow
from zope.interface import implements
from voteit.core.models.interfaces import IWorkflowAware


class WorkflowAware(object):
    """ Mixin class to make content workflow-aware. See IWorkflowAware """
    implements(IWorkflowAware)

    @property
    def workflow(self):
        #wf = getattr(self, '_workflow', None)
        #if wf is None:
        #    wf = self.initialize_workflow()
        
        return get_workflow(self.__class__, self.__class__.__name__, self)

    def initialize_workflow(self):
        #FIXME: the type should be som generic instead of the class name, but since the wrong workflow is returned this is is a workaround
        workflow = get_workflow(self.__class__, self.__class__.__name__, self)
        if workflow:
            workflow.initialize(self)
            #self._workflow = workflow
            return workflow
        
    def get_workflow_state(self):
        return self.workflow.state_of(self)
        
    def set_workflow_state(self, request, state):
        self.workflow.transition_to_state(self, request, state)

    def make_workflow_transition(self, request, transition):
        self.workflow.transition(self, request, transition)
            
    def get_available_workflow_states(self, request):
        states = self.workflow.state_info(self, request)
        astates = []
        for state in states:
            if state['transitions']:
                astates.append(state)
        return astates
