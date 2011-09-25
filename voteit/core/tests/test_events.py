import unittest

from pyramid import testing
from zope.interface.verify import verifyObject


class WorkflowStateChangeTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.events import WorkflowStateChange
        return WorkflowStateChange

    def test_interface(self):
        from voteit.core.interfaces import IWorkflowStateChange
        obj = self._cut(None, 'old_state', 'new_state')
        self.failUnless(verifyObject(IWorkflowStateChange, obj))


class ObjectUpdatedEventTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.events import ObjectUpdatedEvent
        return ObjectUpdatedEvent

    def test_interface(self):
        from voteit.core.interfaces import IObjectUpdatedEvent
        obj = self._cut(None)
        self.failUnless(verifyObject(IObjectUpdatedEvent, obj))
