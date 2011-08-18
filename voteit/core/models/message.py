import pytz
from uuid import uuid4

from sqlalchemy import Table, Column
from sqlalchemy import Integer, Unicode, DateTime, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from zope.component import getUtility
from zope.interface import implements
from zope.component.event import objectEventNotify
from repoze.folder import unicodify
from repoze.folder.events import ObjectAddedEvent
from pyramid.threadlocal import get_current_registry

from voteit.core import RDB_Base
from voteit.core.models.interfaces import IMessages
from voteit.core.models.interfaces import IDateTimeUtil
from voteit.core.models.interfaces import IMessage
from voteit.core.models.unread import Unreads
from voteit.core.models.date_time_util import utcnow


messages_tags = Table('messages_tags', RDB_Base.metadata,
    Column('message_id', Integer, ForeignKey('messages.id')),
    Column('tag_id', Integer, ForeignKey('message_tags.id'))
)

class Message(RDB_Base):
    """ Persistance for a message.
    """
    implements(IMessage)

    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    uid = Column(Unicode(40))
    meetinguid = Column(Unicode(40))
    message = Column(Unicode(250))
    tags = relationship("MessageTag", secondary=messages_tags, backref="messages")
    contextuid = Column(Unicode(40))
    userid = Column(Unicode(100))
    popup = Column(Boolean())
    created = Column(DateTime())

    
    def __init__(self, meetinguid, message, tags=(), contextuid=None, userid=None, popup=False, created=None):
        if not created:
            created = utcnow()
            
        self.uid = unicode(uuid4())
        self.meetinguid = unicodify(meetinguid)
        self.message = unicodify(message)
        self.tags.extend(tags)
        self.contextuid = unicodify(contextuid)
        self.userid = unicodify(userid)
        self.popup = popup
        self.created = created

        objectEventNotify(ObjectAddedEvent(self, self.contextuid, self.uid))
    
    @property
    def string_tags(self):
        """ The tags attribute consists of Tag objects rather than the actual text tags.
            This property returns the text.
        """
        return tuple([x.tag for x in self.tags])
        
    def format_created(self):
        """ Lordag 3 apr 2010, 01:10
        """
        registry = get_current_registry()
        dt_util = registry.getUtility(IDateTimeUtil)
        return dt_util.dt_format(dt_util.localize(self.created, pytz.utc))


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
            query = query.filter(Message.tags.any(MessageTag.tag.in_(tags)))
    
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
        query = query.filter(Message.userid==userid)
        messages = tuple(query.all())

        unread_count = 0
        unreads = Unreads(self.session)
        for message in messages:
            if len(unreads.retrieve(message.userid, message.uid)) > 0:
                unread_count = unread_count + 1
        
        return unread_count

    def tag_to_obj(self, tag):
        query = self.session.query(MessageTag).filter(MessageTag.tag==tag)
        if query.count() > 0:
            return query.one()

        return None