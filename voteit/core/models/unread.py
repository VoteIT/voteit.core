from datetime import datetime

from sqlalchemy import Integer, Unicode, DateTime, Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from zope.interface import implements
from repoze.folder import unicodify

from voteit.core import RDB_Base
from voteit.core.models.interfaces import IUnreads


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
            self.created = datetime.now()
        
    def format_created(self):
        """ Lordag 3 apr 2010, 01:10
        """
        return self.created.strftime("%A %d %B %Y, %H:%M")
        

class Unreads(object):
    """ Handle unreads.
        This behaves like an adapter on a request.
    """
    implements(IUnreads)
    
    def __init__(self, request):
        self.request = request
    
    def add(self, userid, contextuid):
        session = self.request.sql_session
        
        unread = Unread(userid, contextuid)
        session.add(unread)
        
    def remove(self, userid, contextuid):
        session = self.request.sql_session

        read = session.query(Unread).filter(Unread.userid==userid).filter(Unread.contextuid==contextuid).first()
        if read:
            session.delete(read)
            
    def remove_user(self, userid):
        session = self.request.sql_session

        session.query(Unread).filter(Unread.userid==userid).delete()

    def remove_context(self, contextuid):
        session = self.request.sql_session

        session.query(Unread).filter(Unread.contextuid==contextuid).delete()

    def retrieve(self, userid, contextuid=None):
        session = self.request.sql_session

        query = session.query(Unread).filter(Unread.userid==userid)
        if contextuid:
            query = query.filter(Unread.contextuid==contextuid)

        query.order_by('created')

        return tuple(query.all())
