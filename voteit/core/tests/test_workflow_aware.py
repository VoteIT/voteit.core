

import unittest

from pyramid import testing
from zope.interface.verify import verifyObject




class WorkflowAwareTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.workflow_aware import WorkflowAware
        return WorkflowAware()
    
    def test_verify_interface(self):
        from voteit.core.models.interfaces import IWorkflowAware
        self.assertTrue(verifyObject(IWorkflowAware, self._make_obj()))