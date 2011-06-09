from datetime import datetime

from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import DateTime
from sqlalchemy import Column
from zope.interface import implements
from repoze.folder import unicodify

from voteit.core import RDB_Base
from voteit.core.models.interfaces import IMessages


class Message(RDB_Base):
    """ Persistance for an message.
    """
    
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    meetinguid = Column(Unicode(40))
    message = Column(Unicode(250))
    tag = Column(Unicode(10))
    contextuid = Column(Unicode(40))
    userid = Column(Unicode(100))
    created = Column(DateTime())
    
    def __init__(self, meetinguid, message, tag=None, contextuid=None, userid=None, created=datetime.now()):
        self.meetinguid = unicodify(meetinguid)
        self.message = unicodify(message)
        self.tag = unicodify(tag)
        self.contextuid = unicodify(contextuid)
        self.userid = unicodify(userid)
        self.created = created
        
    def format_created(self):
        """ Lordag 3 apr 2010, 01:10
        """
        return self.created.strftime("%A %d %B %Y, %H:%M")

class Messages(object):
    """ Handle messages.
        This behaves like an adapter on a request.
    """
    implements(IMessages)
    
    def __init__(self, request):
        self.request = request
    
    def add(self, meetinguid, message, tag=None, contextuid=None, userid=None):
        session = self.request.sql_session
        
        msg = Message(meetinguid, message, tag, contextuid, userid)
        session.add(msg)

    def retrieve_messages(self, meetinguid, tag=None, contextuid=None, userid=None):
        session = self.request.sql_session
        query = session.query(Message).filter_by(meetinguid=meetinguid)
        if tag:
            query = query.filter_by(tag=tag)
        if contextuid:
            query = query.filter_by(contextuid=contextuid)
        if userid:
            query = query.filter_by(userid=userid)

        query.order_by('created')

        return tuple(query.all())
