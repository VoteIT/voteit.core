from zope.interface import implements
from voteit.core.models.interfaces import ISQLSession
from zope.sqlalchemy.datamanager import ZopeTransactionExtension
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.orm import scoped_session


class SQLSession(object):
    implements(ISQLSession)
    
    def __init__(self, engine):
        self.engine = engine
        self.session_factory = scoped_session(sessionmaker(bind=engine,
                                                           extension=ZopeTransactionExtension()))
    
    def __call__(self):
        return self.session_factory()
