from voteit.core.app import add_sql_session_util
from voteit.core.app import populate_sql_database
from voteit.core.models.interfaces import ISQLSession


def testing_sql_session(config):
    add_sql_session_util(config, sqlite_file='sqlite://') #// means in memory
    populate_sql_database(config)
    return config.registry.getUtility(ISQLSession)() #Returns a session