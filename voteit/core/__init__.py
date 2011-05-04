from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import AuthTktAuthenticationPolicy
from repoze.zodbconn.finder import PersistentApplicationFinder
from zope.component import getGlobalSiteManager


PROJECTNAME = 'voteit.core'
#Must be before all of this packages imports
VoteITMF = TranslationStringFactory(PROJECTNAME)

from voteit.core.models.site import SiteRoot
from voteit.core.models.users import Users


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    groupfinder = None #FIXME
    authn_policy = AuthTktAuthenticationPolicy(secret='sosecret',
                                               callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()

    zodb_uri = settings.get('zodb_uri')
    if zodb_uri is None:
        raise ValueError("No 'zodb_uri' in application configuration.")

    finder = PersistentApplicationFinder(zodb_uri, appmaker)
    def get_root(request):
        return finder(request.environ)
    globalreg = getGlobalSiteManager()
    config = Configurator(registry=globalreg)
    config.setup_registry(settings=settings,
                          root_factory=get_root,
                          authentication_policy=authn_policy,
                          authorization_policy=authz_policy
                          )
    config.add_static_view('static', '%s:static' % PROJECTNAME)
    config.add_static_view('deform', 'deform:static')
    
    #config.add_translation_dirs('%s:locale/' % PROJECTNAME)

    
    config.scan(PROJECTNAME)
    return config.make_wsgi_app()


def appmaker(zodb_root):
    if not 'app_root' in zodb_root:
        app_root = SiteRoot()
        app_root['users'] = Users()
        zodb_root['app_root'] = app_root
        import transaction
        transaction.commit()
    return zodb_root['app_root']
