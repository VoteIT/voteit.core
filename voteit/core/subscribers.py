import sqlite3

from pyramid.events import NewRequest
from pyramid.events import subscriber
from pyramid.events import ApplicationCreated

@subscriber(ApplicationCreated)
def init_sql_database(event):
    #
#    DROP TABLE pending_meeting_access_requests;

    init_query = """
    CREATE TABLE IF NOT EXISTS pending_meeting_access_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_uid CHAR(40) NOT NULL,
        userid CHAR(100) NOT NULL,
        message CHAR(2000) NOT NULL
    );
    """
    sqlite_file = event.app.registry.settings['sqlite_file']
    sqldb = sqlite3.connect(sqlite_file)
    sqldb.executescript(init_query)
    sqldb.commit()

@subscriber(NewRequest)
def connect_sql(event):
    """ Adds property sqldb to a Pyramid request object. """
    request = event.request
    sqlite_file = request.registry.settings['sqlite_file']
    request.sqldb = sqlite3.connect(sqlite_file)
    request.add_finished_callback(close_sql_connection)

def close_sql_connection(request):
    request.sqldb.close()