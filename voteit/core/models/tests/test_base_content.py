import unittest
from datetime import datetime

from pyramid import testing
from voteit.core.testing_helpers import bootstrap_and_fixture
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from voteit.core.models.interfaces import IBaseContent


class BaseContentTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.base_content import BaseContent
        return BaseContent

    def _make_schema(self):
        import colander
        class Schema(colander.Schema):
            title = colander.SchemaNode(colander.String())
            number = colander.SchemaNode(colander.Integer())
        return Schema()

    def test_verify_class(self):
        self.failUnless(verifyClass(IBaseContent, self._cut))

    def test_verify_obj(self):
        self.failUnless(verifyObject(IBaseContent, self._cut()))
    
    def test_uid_generated(self):
        obj = self._cut()
        self.failIf(obj.uid is None)
        self.assertTrue(isinstance(obj.uid, unicode))
    
    def test_uid_compare(self):
        obj1 = self._cut()
        obj2 = self._cut()
        self.assertNotEqual(obj1, obj2)

    def test_creators(self):
        obj = self._cut()
        self.assertEqual(obj.creators, ())
        obj.creators = ['franz']
        self.assertEqual(obj.creators, ('franz',))

    def test_creators_from_request(self):
        self.config.testing_securitypolicy(userid='mr_tester')
        request = testing.DummyRequest()
        self.config = testing.setUp(registry = self.config.registry, request = request)
        self.config.include('arche.testing')
        obj = self._cut()
        self.assertEqual(obj.creators, ('mr_tester',))

    def test_description_property(self):
        obj = self._cut()
        obj.description = "Something"
        self.assertEqual(obj.description, "Something")

    def test_created_property(self):
        now = datetime.now()
        obj = self._cut()
        obj.created = now
        self.assertEqual(obj.created, now)

    def test_modified_property(self):
        now = datetime.now()
        obj = self._cut()
        obj.modified = now
        self.assertEqual(obj.modified, now)

    def test_uid_property(self):
        obj = self._cut()
        obj.uid = "Something_None_unicode"
        self.assertEqual(obj.uid, u"Something_None_unicode")
        self.assertTrue(isinstance(obj.uid, unicode))

    def test_get_set_field_value(self):
        obj = self._cut()
        obj.set_field_value('title', "Hello world")
        self.assertEqual(obj.get_field_value('title'), "Hello world")
        
    def test_get_field_appstruct(self):
        obj = self._cut()
        obj.set_field_value('title', 'Hello')
        obj.set_field_value('number', 1)
        schema = self._make_schema()
        appstruct = obj.get_field_appstruct(schema)
        self.assertEqual(appstruct, {'title':'Hello', 'number':1})

    def test_get_field_appstruct_nonexistent(self):
        """ Check that appstruct doesn't return a value if nothing exists. """
        obj = self._cut()
        obj.set_field_value('title', 'Hello') 
        schema = self._make_schema()
        appstruct = obj.get_field_appstruct(schema)
        self.assertEqual(appstruct, {'title':'Hello'})

    def test_get_field_appstruct_with_none(self):
        """ Check that None is treated as a value. """
        obj = self._cut()
        obj.set_field_value('title', None) 
        schema = self._make_schema()
        appstruct = obj.get_field_appstruct(schema)
        self.assertEqual(appstruct, {'title':None})
        
    def test_set_field_appstruct(self):
        obj = self._cut()
        appstruct = {'title':'Hello', 'number':2}
        obj.set_field_appstruct(appstruct)
        self.assertEqual(obj.get_field_value('title'), 'Hello')
        self.assertEqual(obj.get_field_value('number'), 2)

    def test_set_restricted_key_with_set_field_appstruct(self):
        obj = self._cut()
        appstruct = {'title':'Hello', 'number':2, 'csrf_token':"don't save me"}
        obj.set_field_appstruct(appstruct)
        self.assertEqual(obj.get_field_value('csrf_token'), None)

    def test_set_restricted_key_with_set_field(self):
        obj = self._cut()
        obj.set_field_value('csrf_token', "don't save me")
        self.assertEqual(obj.get_field_value('csrf_token'), None)
    
    def test_get_content_sorting(self):
        parent = self._cut()
        obj1 = self._cut()
        obj1.title = 'hello'
        parent['1'] = obj1
        obj2 = self._cut()
        obj2.title = 'world'
        parent['2'] = obj2
        
        self.assertEqual(parent.get_content(sort_on = 'title'), (obj1, obj2))
        self.assertEqual(parent.get_content(sort_on = 'title', sort_reverse = True), (obj2, obj1))
        self.assertRaises(AttributeError, parent.get_content, sort_on = 'non_existent')
        
    def test_get_content_states(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting.title = 'Hello Meeting'
        ai1 = AgendaItem()
        ai1.title = 'Stuff to do'
        ai2 = AgendaItem()
        ai2.title = 'More important things'
        meeting['ai1'] = ai1
        meeting['ai2'] = ai2
        meeting['b1'] = self._cut()
        
        self.assertEqual(meeting.get_content(sort_on = 'title', states='private'), (ai2, ai1))
        self.assertEqual(meeting.get_content(sort_on = 'title', states=('private', 'upcoming')), (ai2, ai1))
        request = testing.DummyRequest()
        ai1.set_workflow_state(request, 'upcoming')
        self.assertEqual(meeting.get_content(sort_on = 'title', states='private'), (ai2,))
        self.assertEqual(meeting.get_content(sort_on = 'title', states=('private', 'some_other')), (ai2,))
        self.assertEqual(meeting.get_content(sort_on = 'title', states=('private', 'upcoming',)), (ai2, ai1))

    def test_get_content_specific_content_type(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        meeting = Meeting()
        meeting['ai1'] = AgendaItem()
        meeting['ai2'] = AgendaItem()
        meeting['b1'] = self._cut()
        res = meeting.get_content(content_type = 'AgendaItem')
        self.assertEqual(len(res), 2)

    def test_get_content_by_interface(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.interfaces import IAgendaItem
        from voteit.core.models.interfaces import IBaseContent
        meeting = Meeting()
        meeting['ai1'] = AgendaItem()
        meeting['ai2'] = AgendaItem()
        meeting['b1'] = self._cut()
        res = meeting.get_content(iface = IAgendaItem)
        self.assertEqual(len(res), 2)
        #IAgendaItem subclasses IBaseContent
        res = meeting.get_content(iface = IBaseContent)
        self.assertEqual(len(res), 3)

    def test_get_content_limit_results(self):
        parent = self._cut()
        parent['1'] = self._cut()
        parent['2'] = self._cut()
        parent['3'] = self._cut()
        self.assertEqual(len(parent.get_content(limit = 1)), 1)
