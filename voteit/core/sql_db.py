from pyramid.events import NewRequest
from pyramid.events import subscriber


@subscriber(NewRequest)
def connect_sql(event):
    """ Adds property sqldb to a Pyramid request object. """
    request = event.request
    request.sql_session = request.registry.settings['sql_session']
