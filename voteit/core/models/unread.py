from sqlalchemy import Integer, Unicode, DateTime, Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from zope.component import getUtility
from zope.interface import implements
from repoze.folder import unicodify

from voteit.core import RDB_Base
from voteit.core.models.interfaces import IUnreads
from voteit.core.models.date_time_util import utcnow


class Unread(RDB_Base):
    """ Persistance for a unread.
    """
    
    __tablename__ = 'unreads'
    id = Column(Integer, primary_key=True)
    userid = Column(Unicode(100))
    contextuid = Column(Unicode(40))
    created = Column(DateTime())
    
    def __init__(self, userid, contextuid, created=None):
        self.userid = unicodify(userid)
        self.contextuid = unicodify(contextuid)
        if created:
            self.created = created
        else:
            self.created = utcnow()
        
    def format_created(self):
        """ Lordag 3 apr 2010, 01:10
        """
        return self.created.strftime("%A %d %B %Y, %H:%M")
        

class Unreads(object):
    """ Handle unreads.
        This behaves like an adapter on a sql db session.
    """
    implements(IUnreads)
    
    def __init__(self, session):
        self.session = session
    
    def add(self, userid, contextuid):
        unread = Unread(userid, contextuid)
        self.session.add(unread)
        
    def remove(self, userid, contextuid):
        read = self.session.query(Unread).filter(Unread.userid==userid).filter(Unread.contextuid==contextuid).first()
        if read:
            self.session.delete(read)
            
    def remove_user(self, userid):
        self.session.query(Unread).filter(Unread.userid==userid).delete()

    def remove_context(self, contextuid):
        self.session.query(Unread).filter(Unread.contextuid==contextuid).delete()

    def retrieve(self, userid, contextuid=None):
        query = self.session.query(Unread).filter(Unread.userid==userid)
        if contextuid:
            query = query.filter(Unread.contextuid==contextuid)

        query.order_by('created')

        return tuple(query.all())
