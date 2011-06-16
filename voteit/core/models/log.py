from datetime import datetime

from sqlalchemy import Table, Column
from sqlalchemy import Integer, Unicode, DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from zope.interface import implements
from repoze.folder import unicodify

from voteit.core import RDB_Base
from voteit.core.models.interfaces import ILogs

log_tags = Table('log_tags', RDB_Base.metadata,
    Column('log_id', Integer, ForeignKey('logs.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Log(RDB_Base):
    """ Persistance for a log entries.
    """
    
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True)
    meetinguid = Column(Unicode(40))
    message = Column(Unicode(250))
    userid = Column(Unicode(100))
    created = Column(DateTime())
    tags = relationship("Tag", secondary=log_tags, backref="logs")
    primaryuid = Column(Unicode(100))
    secondaryuid = Column(Unicode(100))
    
    def __init__(self, meetinguid, message, tags=None, userid=None, primaryuid=None, secondaryuid=None, created=None):
        if not created:
            created = datetime.now()
    
        self.meetinguid = unicodify(meetinguid)
        self.message = unicodify(message)
        self.userid = unicodify(userid)
        self.created = created
        self.tags = tags
        self.primaryuid = primaryuid
        self.secondaryuid = secondaryuid
        
    def format_created(self):
        """ Lordag 3 apr 2010, 01:10
        """
        return self.created.strftime("%A %d %B %Y, %H:%M")
        
        
class Tag(RDB_Base):
        
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    tag = Column(Unicode(10))
    
    def __init__(self, tag):
        self.tag = tag
    
class Logs(object):
    """ Handle logs.
        This behaves like an adapter on a request.
    """
    implements(ILogs)
    
    def __init__(self, request):
        self.request = request
    
    def add(self, meetinguid, message, tags=None, userid=None, primaryuid=None, secondaryuid=None):
        session = self.request.sql_session
        
        if not type(tags) == tuple:
            tags = (tags, )
        
        _tags = []
        for tag in tags:
            _tag = session.query(Tag).filter(Tag.tag==tag).one()
            _tags.append(_tag)
        
        log = Log(meetinguid, message, _tags, userid, primaryuid, secondaryuid)
        session.add(log)

    def retrieve_entries(self, meetinguid, tag=None, userid=None, primaryuid=None, secondaryuid=None):
        session = self.request.sql_session
        query = session.query(Log).filter(Log.meetinguid==meetinguid)
        if tag:
            query = query.filter(Log.tags.any(tag=tag))
        if userid:
            query = query.filter(Log.userid==userid)
        if primaryuid:
            query = query.filter(Log.primaryuid==primaryuid)
        if secondaryuid:
            query = query.filter(Log.secondaryuid==secondaryuid)

        query.order_by('created')

        return tuple(query.all())
