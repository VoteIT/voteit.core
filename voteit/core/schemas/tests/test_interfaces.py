""" These tests are to make sure schema interfaces work the expected way.
"""
import unittest

from pyramid import testing
from betahaus.pyracont.factories import createSchema
from betahaus.pyracont.interfaces import ISchemaCreatedEvent

from voteit.core.schemas.interfaces import ISchema
from voteit.core.schemas.interfaces import IEditUserSchema


class SchemaInterfaceTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_schema_provides_interface(self):
        self.config.scan('voteit.core.schemas.user')
        schema = createSchema('EditUserSchema')
        self.failUnless(ISchema.providedBy(schema))
        self.failUnless(IEditUserSchema.providedBy(schema))

    def test_subscriber_integration(self):
        self.config.scan('voteit.core.schemas.user')
        L = []
        def subscriber(obj, event):
            L.append((obj, event))
        self.config.add_subscriber(subscriber, [IEditUserSchema, ISchemaCreatedEvent])
        createSchema('EditUserSchema')
        self.failUnless(len(L))
