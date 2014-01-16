from zope.interface import implementer

from voteit.core.interfaces import IWorkflowStateChange
from voteit.core.interfaces import IObjectUpdatedEvent
from voteit.core.interfaces import ILoginSchemaCreated
from voteit.core.interfaces import IRegisterSchemaCreated


@implementer(IWorkflowStateChange)
class WorkflowStateChange(object):
    
    def __init__(self, object, old_state, new_state):
        self.object = object
        self.old_state = old_state
        self.new_state = new_state


@implementer(IObjectUpdatedEvent)
class ObjectUpdatedEvent(object):
    
    def __init__(self, object, indexes=(), metadata=True):
        self.object = object
        self.indexes = indexes
        self.metadata = metadata


@implementer(ILoginSchemaCreated)
class LoginSchemaCreated(object):

    def __init__(self, schema, method):
        self.schema = schema
        self.method = method


@implementer(IRegisterSchemaCreated)
class RegisterSchemaCreated(object):

    def __init__(self, schema, method):
        self.schema = schema
        self.method = method
