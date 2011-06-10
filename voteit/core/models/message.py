from datetime import datetime

from sqlalchemy import Integer, Unicode, DateTime, Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from zope.interface import implements
from repoze.folder import unicodify

from voteit.core import RDB_Base
from voteit.core.models.interfaces import IMessages


class Message(RDB_Base):
    """ Persistance for a message.
    """
    
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    meetinguid = Column(Unicode(40))
    message = Column(Unicode(250))
    tag = Column(Unicode(10))
    contextuid = Column(Unicode(40))
    userid = Column(Unicode(100))
    created = Column(DateTime())
    read = relationship("MessageRead", backref="parent")
    
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
        

class MessageRead(RDB_Base):
    """ Persistance for a message.
    """
    
    __tablename__ = 'messagesread'
    id = Column(Integer, primary_key=True)
    messageid = Column(Integer, ForeignKey('messages.id'))
    userid = Column(Unicode(100))
    read = Column(Boolean)
    
    #TODO: make messageid + userid unique

    def __init__(self, userid, messageid, read=False):
        self.messageid = unicodify(messageid)
        self.userid = unicodify(userid)
        self.read = read


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
        query = session.query(Message).outerjoin((MessageRead, Message.id==MessageRead.messageid)).filter(Message.meetinguid==meetinguid)
        if tag:
            query = query.filter(Message.tag==tag)
        if contextuid:
            query = query.filter(Message.contextuid==contextuid)
        if userid:
            query = query.filter(Message.userid==userid)

        query.order_by('created')

        return tuple(query.all())
        
    def mark_read(self, messageid, userid):
        session = self.request.sql_session
        read = session.query(MessageRead).filter(MessageRead.userid==userid).filter(MessageRead.messageid==messageid).first()
        if read:
            read.read = True
            session.add(read)
        else:
            read = MessageRead(userid, messageid, True)
            session.add(read)
