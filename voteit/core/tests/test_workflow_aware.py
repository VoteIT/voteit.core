import unittest

from pyramid import testing
from zope.interface.verify import verifyObject
from repoze.workflow.workflow import WorkflowError


class WorkflowAwareTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        """ WorkflowAware is a mixin class. We'll use an Agenda item to test. """
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem()
    
    def test_verify_interface(self):
        from voteit.core.models.interfaces import IWorkflowAware
        self.assertTrue(verifyObject(IWorkflowAware, self._make_obj()))

    def test_workflow_not_found(self):
        from voteit.core.models.workflow_aware import WorkflowAware
        obj = WorkflowAware()
        try:
            obj.workflow
            self.fail("Didn't raise workflow error for a content type that didn't have a workflow")
        except WorkflowError:
            pass

