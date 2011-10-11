import unittest

from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Authenticated
from pyramid.url import resource_url
from zope.interface.verify import verifyObject

from voteit.core import security

admin = set([security.ROLE_ADMIN])
moderator = set([security.ROLE_MODERATOR])
participant = set([security.ROLE_PARTICIPANT])
viewer = set([security.ROLE_VIEWER])
owner = set([security.ROLE_OWNER])


class ProposalTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.proposal import Proposal
        return Proposal()
    
    def test_verify_implementation(self):
        from voteit.core.models.interfaces import IProposal
        obj = self._make_obj()
        self.assertTrue(verifyObject(IProposal, obj))
        
    def test_transform_title_subscriber(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)

        self.config.scan('voteit.core.models.site')
        self.config.scan('voteit.core.models.user')
        self.config.scan('voteit.core.models.users')        
        self.config.scan('voteit.core.subscribers.transform_text')
        self.config.include('voteit.core.models.user_tags')
        self.config.include('voteit.core.models.catalog')
        self.config.scan('betahaus.pyracont.fields.password')

        from voteit.core.bootstrap import bootstrap_voteit
        self.root = bootstrap_voteit(echo=False)
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        self.root['m1'] = meeting
        
        obj = self._make_obj()
        obj.set_field_value('title', 'test\ntest')
        meeting['p1'] = obj
        self.assertEqual(obj.get_field_value('title'), 'test<br />\ntest')

        obj = self._make_obj()
        obj.set_field_value('title', 'http://www.voteit.se')
        meeting['p2'] = obj
        self.assertEqual(obj.get_field_value('title'), '<a href="http://www.voteit.se">http://www.voteit.se</a>')
        
        obj = self._make_obj()
        obj.set_field_value('title', '@admin')
        meeting['p3'] = obj
        title = '<a href="%s_userinfo?userid=%s" title="%s" class="inlineinfo">@%s</a>' % (
                resource_url(meeting, request),
                'admin',
                self.root.users['admin'].title,
                'admin',
            )
        self.assertEqual(obj.get_field_value('title'), title)


class ProposalPermissionTests(unittest.TestCase):
    """ Check permissions in different meeting and agenda item states.
        Note that the add permission is handled by the agenda item / meeting.
    """

    def setUp(self):
        self.config = testing.setUp()
        policy = ACLAuthorizationPolicy()
        self.pap = policy.principals_allowed_by_permission
        # load workflow
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.proposal import Proposal
        return Proposal()
    
    def _make_ai(self):
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem()

    def test_published(self):
        obj = self._make_obj()

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Retract
        self.assertEqual(self.pap(obj, security.RETRACT), admin | moderator | owner)

    def test_retracted_in_ongoing_ai(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'retracted')
        ai = self._make_ai()
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        ai['prop'] = obj

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Retract
        self.assertEqual(self.pap(obj, security.RETRACT), set())

    def test_retracted_in_closed_ai(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'retracted')
        ai = self._make_ai()
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        ai.set_workflow_state(request, 'closed')
        ai['prop'] = obj

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), set())

        #Retract
        self.assertEqual(self.pap(obj, security.RETRACT), set())

    def test_unhandled_in_closed_ai(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'unhandled')
        ai = self._make_ai()
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        ai.set_workflow_state(request, 'closed')
        ai['prop'] = obj

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), set())

        #Retract
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
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Retract
        self.assertEqual(self.pap(obj, security.RETRACT), set())

    def test_approved_in_closed_ai(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'voting')
        obj.set_workflow_state(request, 'approved')
        ai = self._make_ai()
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        ai.set_workflow_state(request, 'closed')
        ai['prop'] = obj

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), set())

    def test_denied_in_ongoing_ai(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'voting')
        obj.set_workflow_state(request, 'denied')
        ai = self._make_ai()
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        ai['prop'] = obj

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Retract
        self.assertEqual(self.pap(obj, security.RETRACT), set())
