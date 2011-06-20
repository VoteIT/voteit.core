from pyramid.i18n import TranslationStringFactory
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from repoze.zodbconn.finder import PersistentApplicationFinder
from pyramid.config import Configurator

from sqlalchemy import MetaData
from sqlalchemy.orm import scoped_session
from sqlalchemy.ext.declarative import declarative_base

#Must be before all of this packages imports since some other methods might import it
PROJECTNAME = 'voteit.core'
VoteITMF = TranslationStringFactory(PROJECTNAME)
RDB_Base = declarative_base()


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    from voteit.core.security import groupfinder
    #FIXME: Is secret a salt or an id?
    authn_policy = AuthTktAuthenticationPolicy(secret='sosecret',
                                               callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()

    zodb_uri = settings.get('zodb_uri')
    if zodb_uri is None:
        raise ValueError("No 'zodb_uri' in application configuration.")

    finder = PersistentApplicationFinder(zodb_uri, appmaker)
    def get_root(request):
        return finder(request.environ)

    sessionfact = UnencryptedCookieSessionFactoryConfig('messages')

    from voteit.core import app
    app.init_sql_database(settings)
    
    config = Configurator(settings=settings,
                          root_factory=get_root,
                          authentication_policy=authn_policy,
                          authorization_policy=authz_policy,
                          session_factory = sessionfact,)
    
    config.add_static_view('static', '%s:static' % PROJECTNAME)
    config.add_static_view('deform', 'deform:static')

    #Set which mailer to use        
    config.include(settings['mailer'])

    app.register_content_types(config)
    app.register_poll_plugins(config)
    app.register_request_factory(config)
    
    #config.add_translation_dirs('%s:locale/' % PROJECTNAME)

    config.scan(PROJECTNAME)

    config.hook_zca()

    return config.make_wsgi_app()


def appmaker(zodb_root):
    if not 'app_root' in zodb_root:
        from voteit.core.bootstrap import bootstrap_voteit
        zodb_root['app_root'] = bootstrap_voteit() #Returns a site root
        import transaction
        transaction.commit()
    return zodb_root['app_root']


