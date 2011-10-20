from transaction import commit
from repoze.zodbconn.uri import db_from_uri

from voteit.core.bootstrap import bootstrap_voteit


def dummy_zodb_root(config):
    """ Returns a bootstrapped root object that has been attached to
        a ZODB database that only exist in memory. It will behave
        the same way as a database that would be stored permanently.
    """

    db = db_from_uri('memory://')
    conn = db.open()
    zodb_root = conn.root()
    zodb_root['app_root'] = bootstrap_and_fixture(config)
    commit()
    return zodb_root['app_root']


def bootstrap_and_fixture(config):
    config.include('pyramid_zcml')
    config.load_zcml('voteit.core:configure.zcml')
    config.scan('voteit.core.models.site')
    config.scan('voteit.core.models.user')
    config.scan('voteit.core.models.users')
    config.scan('betahaus.pyracont.fields.password')
    return bootstrap_voteit(echo=False)
