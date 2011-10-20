from unittest import TestCase

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


class CatalogSubscriberTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.scan('voteit.core.subscribers.catalog')
        self.config.include('voteit.core.models.user_tags')
        self.config.include('voteit.core.models.catalog')

    def tearDown(self):
        testing.tearDown()

    def _fixture(self):
        return bootstrap_and_fixture(self.config)

    @property
    def _ai(self):
        """ Has metadata enabled """
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem

    def _metadata_for_query(self, root, **kw):
        from voteit.core.models.catalog import metadata_for_query
        return metadata_for_query(root.catalog, **kw)
    
    def test_object_added_catalog(self):
        root = self._fixture()
        text = 'New object'
        root['new_obj'] = self._ai(title = text)
        self.assertEqual(root.catalog.search(title = text)[0], 1)
    
    def test_object_added_metadata(self):
        root = self._fixture()
        text = 'New object'
        root['new_obj'] = self._ai(title = text)
        metadata = self._metadata_for_query(root, title = text)
        self.assertEqual(metadata[0]['title'], text)

    def test_object_updated_wf_changed_catalog(self):
        root = self._fixture()
        request = testing.DummyRequest()
        text = 'New object'
        root['new_obj'] = self._ai(title = text)
        root['new_obj'].set_workflow_state(request, 'upcoming')
        self.assertEqual(root.catalog.search(title = text, workflow_state = 'upcoming')[0], 1)

    def test_object_updated_wf_changed_metadata(self):
        root = self._fixture()
        request = testing.DummyRequest()
        text = 'New object'
        root['new_obj'] = self._ai(title = text)
        root['new_obj'].set_workflow_state(request, 'upcoming')
        metadata = self._metadata_for_query(root, title = text, workflow_state = 'upcoming')
        self.assertEqual(metadata[0]['workflow_state'], 'upcoming')

    def test_object_updated_from_appstruct_catalog(self):
        root = self._fixture()
        ai = self._ai(title = 'New object')
        root['new_obj'] = ai
        ai.set_field_appstruct({'title': 'New title'})
        self.assertEqual(root.catalog.search(title = 'New title')[0], 1)

    def test_object_updated_from_appstruct_metadata(self):
        root = self._fixture()
        ai = self._ai(title = 'New object')
        root['new_obj'] = ai
        ai.set_field_appstruct({'title': 'New title'})
        metadata = self._metadata_for_query(root, uid = ai.uid)
        self.assertEqual(metadata[0]['title'], 'New title')

    def test_object_deleted_from_catalog(self):
        root = self._fixture()
        ai = self._ai(title = 'New object')
        root['new_obj'] = ai
        #Just to make sure
        self.assertEqual(root.catalog.search(uid = ai.uid)[0], 1)
        del root['new_obj']
        self.assertEqual(root.catalog.search(uid = ai.uid)[0], 0)

    def test_object_deleted_from_metadata(self):
        root = self._fixture()
        ai = self._ai(title = 'New object')
        root['new_obj'] = ai
        #Just to make sure
        self.failUnless(self._metadata_for_query(root, uid = ai.uid))
        del root['new_obj']
        self.failIf(self._metadata_for_query(root, uid = ai.uid))
