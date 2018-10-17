import unittest

from arche.resources import Root
from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Authenticated
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from voteit.core import security
from voteit.core.models.interfaces import IProposal


class ProposalTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.proposal import Proposal
        return Proposal

    def test_verify_class(self):
        self.failUnless(verifyClass(IProposal, self._cut))

    def test_verify_obj(self):
        self.failUnless(verifyObject(IProposal, self._cut()))
        
    def test_get_tags(self):
        obj = self._cut()
        obj.text = '#Quisque #aliquam,#ante in #tincidunt #aliquam. #Risus neque#eleifend #nunc'
        tags = obj.tags
        self.assertIn('quisque', tags)
        self.assertIn('aliquam', tags)
        self.assertIn('ante', tags)
        self.assertIn('tincidunt', tags)
        self.assertIn('aliquam', tags)
        self.assertIn('risus', tags)
        self.assertIn('nunc', tags)
        self.assertNotIn('eleifend', tags)
        
    def test_aid_tag(self):
        obj = self._cut()
        obj.set_field_value('aid', "dummyuser-1")
        self.assertIn('dummyuser-1', obj.tags)


admin = set([security.ROLE_ADMIN])
moderator = set([security.ROLE_MODERATOR])
authenticated = set([Authenticated])
discuss = set([security.ROLE_DISCUSS])
propose = set([security.ROLE_PROPOSE])
viewer = set([security.ROLE_VIEWER])
voter = set([security.ROLE_VOTER])
owner = set([security.ROLE_OWNER])


class ProposalPermissionTests(unittest.TestCase):
    """ Check permissions in different meeting and agenda item states.
        Note that the add permission is handled by the agenda item / meeting.
    """

    def setUp(self):
        self.config = testing.setUp()
        policy = ACLAuthorizationPolicy()
        self.pap = policy.principals_allowed_by_permission
        self.config.include('arche.testing')
        self.config.include('voteit.core.testing_helpers.register_workflows')
        self.config.include('arche.models.reference_guard')
        self.config.include('voteit.core.models.agenda_item')
        self.config.include('voteit.core.models.proposal')

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.proposal import Proposal
        return Proposal()
    
    def _make_ai(self):
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem()

    def test_published_in_private_ai(self):
        request = testing.DummyRequest()
        ai = self._make_ai()
        ai['p'] = obj = self._make_obj()
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator)
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)
        self.assertEqual(self.pap(obj, security.RETRACT), admin | moderator)

    def test_published_in_ongoing_ai(self):
        request = testing.DummyRequest()
        ai = self._make_ai()
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        ai['p'] = obj = self._make_obj()
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer )
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)
        self.assertEqual(self.pap(obj, security.RETRACT), admin | moderator | owner )

    def test_retracted_in_ongoing_ai(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'retracted')
        ai = self._make_ai()
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        ai['prop'] = obj

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer )

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Retract
        self.assertEqual(self.pap(obj, security.RETRACT), set())

    def test_retracted_in_closed_ai(self):
        self.config.include('voteit.core.testing_helpers.register_catalog')
        request = testing.DummyRequest()
        root = Root()
        root['ai'] = ai = self._make_ai()
        ai.workflow.do_transition('closed', request)
        ai['prop'] = obj = self._make_obj()
        obj.workflow.do_transition('retracted', request)

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer )

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), set())

        #Retract
        self.assertEqual(self.pap(obj, security.RETRACT), set())

    def test_unhandled_in_closed_ai(self):
        self.config.include('voteit.core.testing_helpers.register_catalog')
        request = testing.DummyRequest()
        root = Root()
        root['ai'] = ai = self._make_ai()
        ai.workflow.do_transition('closed', request)
        ai['prop'] = obj = self._make_obj()
        obj.workflow.do_transition('unhandled', request)
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer )
        self.assertEqual(self.pap(obj, security.EDIT), set())
        self.assertEqual(self.pap(obj, security.DELETE), set())
        self.assertEqual(self.pap(obj, security.RETRACT), set())

    def test_approved_in_ongoing_ai(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'voting')
        obj.set_workflow_state(request, 'approved')
        ai = self._make_ai()
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        ai['prop'] = obj

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer )

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Retract
        self.assertEqual(self.pap(obj, security.RETRACT), set())

    def test_approved_in_closed_ai(self):
        self.config.include('voteit.core.testing_helpers.register_catalog')
        request = testing.DummyRequest()
        root = Root()
        root['ai'] = ai = self._make_ai()
        ai.workflow.do_transition('closed', request)
        ai['prop'] = obj = self._make_obj()
        obj.workflow.do_transition('approved', request)

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer )

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), set())

    def test_denied_in_ongoing_ai(self):
        request = testing.DummyRequest()
        root = Root()
        root['ai'] = ai = self._make_ai()
        ai.workflow.do_transition('ongoing', request)
        ai['prop'] = obj = self._make_obj()
        obj.workflow.do_transition('denied', request)

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer )

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Retract
        self.assertEqual(self.pap(obj, security.RETRACT), set())