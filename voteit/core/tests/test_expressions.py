import unittest

from pyramid import testing

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import Column

from zope.sqlalchemy import ZopeTransactionExtension


class ExpressionTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_create(self):
        from voteit.core.models.expression_adapter import Expression
        exp = Expression('test', 'test@test.com', '123456789')

    def test_read(self):
        from voteit.core.models.expression_adapter import Expression
        import pdb; pdb.set_trace()
        session = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
        exp = Expression('test', 'test@test.com', '123456789')
        session.add(exp)
        session.flush()
        query = session.query(Expression).filter_by(tag='test')

