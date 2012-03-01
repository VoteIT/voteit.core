from pyramid.i18n import TranslationStringFactory
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid_zodbconn import get_connection

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
    config.hook_zca()
    return config.make_wsgi_app()


def default_configurator(settings):
    from voteit.core.security import groupfinder

    #Authentication policies
    authn_policy = AuthTktAuthenticationPolicy(secret=settings['tkt_secret'],
                                               callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()
    sessionfact = UnencryptedCookieSessionFactoryConfig('messages')
    return Configurator(settings=settings,
                        authentication_policy=authn_policy,
                        authorization_policy=authz_policy,
                        root_factory=root_factory,
                        session_factory = sessionfact,)


def required_components(config):
    #Component includes
    config.include('voteit.core.models.user_tags')
    config.include('voteit.core.models.logs')
    config.include('voteit.core.models.date_time_util')
    config.include('voteit.core.models.catalog')
    config.include('voteit.core.models.unread')
    #For password storage
    config.scan('betahaus.pyracont.fields.password')

    cache_ttl_seconds = int(config.registry.settings.get('cache_ttl_seconds', 7200))
    config.add_static_view('static', '%s:static' % PROJECTNAME, cache_max_age = cache_ttl_seconds)
    config.add_static_view('deform', 'deform:static', cache_max_age = cache_ttl_seconds)
    config.add_translation_dirs('deform:locale/',
                                'colander:locale/',
                                '%s:locale/' % PROJECTNAME,)
    config.scan(PROJECTNAME)
    config.include(adjust_default_view_component_order)
    from voteit.core.security import VIEW
    config.set_default_permission(VIEW)    
    config.include(register_plugins)
    config.include(adjust_view_component_order)


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


def root_factory(request):
    conn = get_connection(request)
    return appmaker(conn.root())


def appmaker(zodb_root):
    if not 'app_root' in zodb_root:
        from voteit.core.bootstrap import bootstrap_voteit
        zodb_root['app_root'] = bootstrap_voteit() #Returns a site root
        import transaction
        transaction.commit()
    return zodb_root['app_root']


def adjust_view_component_order(config):
    from betahaus.viewcomponent.interfaces import IViewGroup
    prefix = "vieworder."
    lprefix = len(prefix)
    for (k, v) in config.registry.settings.items():
        if k.startswith(prefix):
            name = k[lprefix:]
            util = config.registry.getUtility(IViewGroup, name = name)
            util.order = v.strip().splitlines()

def adjust_default_view_component_order(config):
    from betahaus.viewcomponent.interfaces import IViewGroup
    from voteit.core.view_component_order import DEFAULT_VC_ORDER
    for (name, items) in DEFAULT_VC_ORDER:
        util = config.registry.getUtility(IViewGroup, name = name)
        util.order = items


def includeme(config):
    """ Called when voteit.core is used as a component of another application.
        It should load its default components, but not make too much assumptions.
        This is also a good plugin point for other applications integration tests.
        It's important that hook_zca is run in the calling package, otherwise
        workflows won't work.
        Compare with startup in main.
        Note that you still need to add all the things added in the default_configurator method.
    """
    config.include(required_components)
