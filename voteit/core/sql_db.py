#FIXME: This file should be considered to be temporary. We'll probably handle this through a lib of some sort

import sqlite3

from pyramid.events import NewRequest
from pyramid.events import subscriber
from pyramid.events import ApplicationCreated


EXPRESSIONS_TABLE_INIT = """
    CREATE TABLE IF NOT EXISTS user_expressions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid CHAR(40) NOT NULL,
        userid CHAR(100) NOT NULL,
        tag CHAR(10) NOT NULL
    );
"""
ACCESS_REQUESTS_TABLE_INIT = """
    CREATE TABLE IF NOT EXISTS pending_meeting_access_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_uid CHAR(40) NOT NULL,
        userid CHAR(100) NOT NULL,
        message CHAR(2000) NOT NULL
    );
"""


@subscriber(ApplicationCreated)
def init_sql_database(event):
    sqlite_file = event.app.registry.settings['sqlite_file']
    
    sqldb = sqlite3.connect(sqlite_file)
    sqldb.executescript(EXPRESSIONS_TABLE_INIT)
    sqldb.executescript(ACCESS_REQUESTS_TABLE_INIT)
    sqldb.commit()
    sqldb.close()

@subscriber(NewRequest)
def connect_sql(event):
    """ Adds property sqldb to a Pyramid request object. """
    request = event.request
    sqlite_file = request.registry.settings['sqlite_file']
    request.sqldb = sqlite3.connect(sqlite_file)
    request.add_finished_callback(close_sql_connection)

def close_sql_connection(request):
    request.sqldb.close()
