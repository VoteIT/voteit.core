

class Expressions(object):
    """ Handle user expressions like 'Like' or 'Support'.
    """
    #FIXME: Some statements here is vulnerable to SQL injections.
    #While this class shouldn't be accessed directly by anything, it might be good
    #to clean it up when we have the time.
    #All SQL-parts should be handled through another lib
    
    def __init__(self, request):
        self.request = request
    
    def add(self, tag, userid, uid):
        self.request.sqldb.execute('insert into user_expressions (uid, userid, tag) values (?, ?, ?)',
                                   [uid, userid, tag])
        self.request.sqldb.commit()

    def retrieve_userids(self, tag, uid):
        query = "select userid from user_expressions where tag = '%s' and uid = '%s';" % (tag, uid)
        result = self.request.sqldb.execute(query)
        userids = set()
        for row in result.fetchall():
            userids.add(row[0])
        return userids

    def remove(self, tag, userid, uid):
        query = "delete from user_expressions where tag = '%s' and userid = '%s' and uid = '%s';" % (tag, userid, uid)
        result = self.request.sqldb.execute(query)
        self.request.sqldb.commit()
