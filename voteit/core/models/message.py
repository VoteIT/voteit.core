from datetime import datetime

from sqlalchemy import Table, Column
from sqlalchemy import Integer, Unicode, DateTime, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from zope.interface import implements
from repoze.folder import unicodify

from voteit.core import RDB_Base
from voteit.core.models.interfaces import IMessages

messages_tags = Table('messages_tags', RDB_Base.metadata,
    Column('message_id', Integer, ForeignKey('messages.id')),
    Column('tag_id', Integer, ForeignKey('message_tags.id'))
)

class Message(RDB_Base):
    """ Persistance for a message.
    """
    
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    meetinguid = Column(Unicode(40))
    message = Column(Unicode(250))
    tags = relationship("MessageTag", secondary=messages_tags, backref="messages")
    contextuid = Column(Unicode(40))
    userid = Column(Unicode(100))
    unread = Column(Boolean())
    popup = Column(Boolean())
    created = Column(DateTime())
    
    def __init__(self, meetinguid, message, tags=(), contextuid=None, userid=None, popup=False, created=None):
        if not created:
            created = datetime.now()
            
        self.meetinguid = unicodify(meetinguid)
        self.message = unicodify(message)
        self.tags.extend(tags)
        self.contextuid = unicodify(contextuid)
        self.userid = unicodify(userid)
        self.unread = True
        self.popup = popup
        self.created = created
    
    @property
    def string_tags(self):
        """ The tags attribute consists of Tag objects rather than the actual text tags.
            This property returns the text.
        """
        return tuple([x.tag for x in self.tags])
        
    def format_created(self):
        """ Lordag 3 apr 2010, 01:10
        """
        return self.created.strftime("%A %d %B %Y, %H:%M")


class MessageTag(RDB_Base):
        
    __tablename__ = 'message_tags'
    id = Column(Integer, primary_key=True)
    tag = Column(Unicode(10))
    
    def __init__(self, tag):
        self.tag = tag


class Messages(object):
    """ Handle messages.
        This behaves like an adapter on a sql db session.
    """
    implements(IMessages)
    
    def __init__(self, session):
        self.session = session
    
    def add(self, meetinguid, message, tags=(), contextuid=None, userid=None):    
        _tags = []
        for tag in tags:
            query = self.session.query(MessageTag).filter(MessageTag.tag==tag)
            if query.count() == 0:
                _tag = MessageTag(tag)
                self.session.add(_tag)
                _tags.append(_tag)
            else:
                _tag = query.one()
                _tags.append(_tag)

        msg = Message(meetinguid, message, _tags, contextuid, userid)
        self.session.add(msg)

    def retrieve_messages(self, meetinguid, tags=(), contextuid=None, userid=None):
        query = self.session.query(Message).filter(Message.meetinguid==meetinguid)
        if tags:
            query = query.filter(Message.tags.any(tags=tags))
        if contextuid:
            query = query.filter(Message.contextuid==contextuid)
        if userid:
            query = query.filter(Message.userid==userid)

        query.order_by('created')

        return tuple(query.all())
        
    def mark_read(self, messageid, userid):
        message = self.session.query(Message).filter(Message.id==messageid).filter(Message.userid==userid).first()
        if message:
            message.unread = False
            self.session.add(message)

    def unreadcount_in_meeting(self, meeting_uid, userid):
        query = self.session.query(Message)
        query = query.filter(Message.meetinguid==meeting_uid)
        query = query.filter(Message.unread==True)
        query = query.filter(Message.userid==userid)
        return len(query.all())
        
