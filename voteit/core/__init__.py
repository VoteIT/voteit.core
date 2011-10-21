from pyramid.i18n import TranslationStringFactory
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from repoze.zodbconn.finder import PersistentApplicationFinder
from pyramid.config import Configurator
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import AuthTktAuthenticationPolicy


#Must be before all of this packages imports since some other methods might import it
PROJECTNAME = 'voteit.core'
VoteITMF = TranslationStringFactory(PROJECTNAME)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
        If you don't want to start the VoteIT app from this method,
        be sure to include the same things at least.
    """
    import voteit.core.patches

    config = default_configurator(settings)
    config.include(required_components)
    config.include(register_plugins)
    config.hook_zca()
    return config.make_wsgi_app()


def default_configurator(settings):
    from voteit.core.security import groupfinder

    #Authentication policies
    authn_policy = AuthTktAuthenticationPolicy(secret=settings['tkt_secret'],
                                               callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()

    zodb_uri = settings.get('zodb_uri')
    if zodb_uri is None:
        raise ValueError("No 'zodb_uri' in application configuration.")

    finder = PersistentApplicationFinder(zodb_uri, appmaker)
    def get_root(request):
        return finder(request.environ)

    sessionfact = UnencryptedCookieSessionFactoryConfig('messages')

    return Configurator(settings=settings,
                        authentication_policy=authn_policy,
                        authorization_policy=authz_policy,
                        root_factory=get_root,
                        session_factory = sessionfact,)


def required_components(config):
    #Component includes
    config.include('voteit.core.models.user_tags')
    config.include('voteit.core.models.logs')
    config.include('voteit.core.models.date_time_util')
    config.include('voteit.core.models.catalog')
    config.include('voteit.core.models.export_import')
    #For password storage
    config.scan('betahaus.pyracont.fields.password')

    #Include all poll plugins from paster .ini config
    config.include(register_poll_plugins)

    config.add_static_view('static', '%s:static' % PROJECTNAME)
    config.add_static_view('deform', 'deform:static')

    #Set which mailer to use
    config.include(config.registry.settings['mailer'])

    config.add_translation_dirs('deform:locale/',
                                'colander:locale/',
                                '%s:locale/' % PROJECTNAME,)
    config.scan(PROJECTNAME)


def register_poll_plugins(config):
    """ Register poll plugins configured in the paster .ini file.
        At least one must be used, otherwise polls won't work.
    """
    poll_plugins = config.registry.settings.get('poll_plugins')
    if poll_plugins is not None:
        for poll_plugin in poll_plugins.strip().splitlines():
            config.include(poll_plugin)
    else:
        raise ValueError("At least one poll plugin must be used")


def register_plugins(config):
    """ Register any plugins specified in paster .init file.
        This could be anything, and they will override applicaton
        configuration, since they're running as the last part.
        This is a good way to tweak any behaviour of VoteIT,
        without actually having to make a whole new configurator yourself.
    """
    plugins = config.registry.settings.get('plugins')
    if plugins is not None:
        for plugin in plugins.strip().splitlines():
            config.include(plugin)


def appmaker(zodb_root):
    if not 'app_root' in zodb_root:
        from voteit.core.bootstrap import bootstrap_voteit
        zodb_root['app_root'] = bootstrap_voteit() #Returns a site root
        import transaction
        transaction.commit()
    return zodb_root['app_root']
