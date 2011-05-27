from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import Column

from voteit.core.models import DBBase

class Expression(object):
    """ """
    
    __tablename__ = 'expressions'
    id = Column(Integer, primary_key=True)
    tag = Column(Unicode(10))
    userid = Column(Unicode(100))
    uid = Column(Unicode(40))
    
    #TODO: make tag+userid+uid unique
    
    def __init__(self, tag, userid, uid):
        self.tag = tag
        self.userid = userid
        self.uid = uid
        
    def __repr__(self):
        return "<Expression('%s','%s','%s')>" % (self.tag, self.userid, self.uid)

class Expressions(object):
    """ Handle user expressions like 'Like' or 'Support'.
    """
    
    def __init__(self, request):
        self.request = request
    
    def add(self, tag, userid, uid):
        session = self.request.sql_session()
        
        exp = Expression(tag, userid, uid)
        session.add(exp)

    def retrieve_userids(self, tag, uid):
        session = self.request.sql_session()
        query = session.query(Expression).filter_by(tag=tag, uid=uid)

        userids = set()
        for row in query.all():
            userids.add(row.userid)
        return userids

    def remove(self, tag, userid, uid):
        session = self.request.sql_session()
        query = session.query(Expression).filter_by(tag=tag, userid=userid, uid=uid)
        exp = query.first()
        session.delete(exp)
