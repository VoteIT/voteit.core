import unittest
import tempfile

from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from transaction import commit
from pyramid.traversal import find_root

from voteit.core.models.interfaces import IExportImport
from voteit.core.bootstrap import bootstrap_voteit
from voteit.core.testing_helpers import dummy_zodb_root


class ExportImportTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _meeting_fixture(self, obj):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        obj['meeting'] = Meeting(creators = ['admin'])
        obj['meeting']['ai']= AgendaItem(creators = ['admin'], title="AI test title")
        commit()
        return obj

    @property
    def _cut(self):
        from voteit.core.models.export_import import ExportImport
        return ExportImport

    def _make_filedata_from_context(self, context):
        """ This will export meeting fixture and take the filedata.
            Instead of shipping a large export file with this package.
        """
        root = find_root(context)
        ei = self._cut(root)
        data_file = tempfile.NamedTemporaryFile(mode = 'wb')
        name = data_file.name
        data_file.write(ei.download_export(context).body)
        data_file.flush()        
        data = {}
        data = open(name, 'rb')
        return data

    def test_verify_class(self):
        self.failUnless(verifyClass(IExportImport, self._cut))

    def test_verify_obj(self):
        self.failUnless(verifyObject(IExportImport, self._cut(None)))

    def test_download_export(self):
        root = dummy_zodb_root(self.config)
        self._meeting_fixture(root)
        ei = self._cut(root)
        result = ei.download_export(root['meeting'])
        self.assertEqual('200 OK', result.status)
        self.assertTrue(result.body.startswith('ZEXP'))

    def test_import_data(self):
        from voteit.core.models.interfaces import IMeeting
        self.config.include('voteit.core.models.catalog')
        self.config.include('voteit.core.models.user_tags')
        root = dummy_zodb_root(self.config)
        self._meeting_fixture(root)
        filedata = self._make_filedata_from_context(root['meeting'])
        ei = self._cut(root)
        ei.import_data(root, 'new_meeting', filedata)
        self.failUnless('new_meeting' in root)
        self.failUnless(IMeeting.providedBy(root['new_meeting']))

    def test_import_data_in_catalog(self):
        self.config.include('voteit.core.models.catalog')
        self.config.include('voteit.core.models.user_tags')
        root = dummy_zodb_root(self.config)
        self._meeting_fixture(root)
        #Catalog won't be updated here
        self.assertEqual(root.catalog.search(content_type = 'AgendaItem')[0], 0)
        filedata = self._make_filedata_from_context(root['meeting'])
        ei = self._cut(root)
        ei.import_data(root, 'new_meeting', filedata)
        self.assertEqual(root.catalog.search(content_type = 'AgendaItem')[0], 1)
