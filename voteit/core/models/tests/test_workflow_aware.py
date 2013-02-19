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

    def _registerEventListener(self, listener, iface):
        from zope.interface import Interface
        self.config.registry.registerHandler(listener, (Interface, iface))

    def test_verify_interface(self):
        from voteit.core.models.interfaces import IWorkflowAware
        self.assertTrue(verifyObject(IWorkflowAware, self._make_obj()))

    def test_workflow_not_found(self):
        from voteit.core.models.workflow_aware import WorkflowAware
        obj = WorkflowAware()
        self.assertRaises(WorkflowError, obj.get_workflow_state) #Has no wf

    def test_workflow_event_on_state_change(self):
        from voteit.core.interfaces import IWorkflowStateChange

        events = []
        def listener(obj, event):
            events.append((obj, event))
        self._registerEventListener(listener, IWorkflowStateChange)
        
        obj = self._make_obj()
        request = testing.DummyRequest()
        obj.set_workflow_state(request, 'upcoming')
        
        event_obj = events[0][0]
        event = events[0][1]
        
        self.assertEqual(event_obj, obj)
        self.assertTrue(IWorkflowStateChange.providedBy(event))
        
    def test_current_state_title(self):
        obj = self._make_obj()
        request = testing.DummyRequest()
        self.assertEqual(obj.current_state_title(request), u'Private')
        obj.set_workflow_state(request, 'upcoming')
        self.assertEqual(obj.current_state_title(request), u'Upcoming')
