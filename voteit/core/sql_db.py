#FIXME: This file should be considered to be temporary. We'll probably handle this through a lib of some sort

import sqlite3

from pyramid.events import NewRequest
from pyramid.events import subscriber
from pyramid.events import ApplicationCreated

#@subscriber(ApplicationCreated)
#def init_sql_database(event):
#    sqlite_file = event.app.registry.settings['sqlite_file']
#    
#    sqldb = sqlite3.connect(sqlite_file)
#    sqldb.executescript(EXPRESSIONS_TABLE_INIT)
#    sqldb.executescript(ACCESS_REQUESTS_TABLE_INIT)
#    sqldb.commit()
#    sqldb.close()

@subscriber(NewRequest)
def connect_sql(event):
    """ Adds property sqldb to a Pyramid request object. """
    request = event.request
#    sqlite_file = request.registry.settings['sqlite_file']
#    request.sqldb = sqlite3.connect(sqlite_file)
#    request.add_finished_callback(close_sql_connection)
    request.sql_session = request.registry.settings['sql_session']
    import pdb; pdb.set_trace()

#def close_sql_connection(request):
#    request.sqldb.close()
