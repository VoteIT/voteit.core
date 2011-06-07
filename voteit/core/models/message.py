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
    userid = Column(Unicode(100))
    message = Column(Unicode(250))
    meeting = Column(Unicode(40))
    created = Column(DateTime())
    
    def __init__(self, userid, message, meeting_uid, created=datetime.now()):
        self.userid = unicodify(userid)
        self.message = unicodify(message)
        self.meeting = unicodify(meeting_uid)
        self.created = created

class Messages(object):
    """ Handle messages.
        This behaves like an adapter on a request.
    """
    implements(IMessages)
    
    def __init__(self, request):
        self.request = request
    
    def add(self, userid, message, meeting_uid):
        session = self.request.sql_session
        
        msg = Message(userid, message, meeting_uid)
        session.add(msg)

    def retrieve_user_messages(self, userid, meeting_uid):
        session = self.request.sql_session
        query = session.query(Message).filter_by(userid=userid, meeting=meeting_uid).order_by('created')

        return tuple(query.all())

    def remove(self, userid, meeting_uid, id):
        session = self.request.sql_session
        query = session.query(Message).filter_by(userid=userid, meeting=meeting_uid, id=id)
        message = query.first()
        session.delete(message)
