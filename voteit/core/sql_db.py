from pyramid.events import NewRequest
from pyramid.events import subscriber


@subscriber(NewRequest)
def connect_sql(event):
    """ Adds property sqldb to a Pyramid request object. """
    make_session(event.request)
    

def make_session(request):
    if not hasattr(request, 'sql_session'):
        request.sql_session = request.registry.settings['rdb_session_factory']()
