from datetime import datetime

from sqlalchemy import Integer, Unicode, DateTime
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from zope.interface import implements
from repoze.folder import unicodify

from voteit.core import RDB_Base
from voteit.core.models.interfaces import ILogs


class Log(RDB_Base):
    """ Persistance for a log entries.
    """
    
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True)
    meetinguid = Column(Unicode(40))
    message = Column(Unicode(250))
    tag = Column(Unicode(10))
    userid = Column(Unicode(100))
    created = Column(DateTime())
    
    def __init__(self, meetinguid, message, tag=None, userid=None, created=datetime.now()):
        self.meetinguid = unicodify(meetinguid)
        self.message = unicodify(message)
        self.tag = unicodify(tag)
        self.userid = unicodify(userid)
        self.created = created
        
    def format_created(self):
        """ Lordag 3 apr 2010, 01:10
        """
        return self.created.strftime("%A %d %B %Y, %H:%M")
        

class Logs(object):
    """ Handle logs.
        This behaves like an adapter on a request.
    """
    implements(ILogs)
    
    def __init__(self, request):
        self.request = request
    
    def add(self, meetinguid, message, tag=None, userid=None):
        session = self.request.sql_session
        
        log = Log(meetinguid, message, tag, userid)
        session.add(log)

    def retrieve_entries(self, meetinguid, tag=None, userid=None):
        session = self.request.sql_session
        query = session.query(Log).filter(Log.meetinguid==meetinguid)
        if tag:
            #FIXME: this should be tag in Log.tag, but I can't find any documentation how 
            # to do it. Log.tag.in_(tag) is the wrong way around
            query = query.filter(Log.tag==tag)
        if userid:
            query = query.filter(Log.userid==userid)

        query.order_by('created')

        return tuple(query.all())
