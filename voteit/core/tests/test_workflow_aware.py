

import unittest

from pyramid import testing
from zope.interface.verify import verifyObject




class WorkflowAwareTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        """ WorkflowAware is a mixin class. """
        from voteit.core.models.workflow_aware import WorkflowAware
        class Dummy(WorkflowAware):
            content_type = 'dummy'
        return Dummy()
    
    def test_verify_interface(self):
        from voteit.core.models.interfaces import IWorkflowAware
        self.assertTrue(verifyObject(IWorkflowAware, self._make_obj()))