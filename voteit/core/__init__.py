from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import AuthTktAuthenticationPolicy
from repoze.zodbconn.finder import PersistentApplicationFinder
from zope.component import getGlobalSiteManager
from zope.interface.verify import verifyClass
from zope.configuration import xmlconfig
from pyramid.threadlocal import get_current_registry

PROJECTNAME = 'voteit.core'
#Must be before all of this packages imports
VoteITMF = TranslationStringFactory(PROJECTNAME)

#voteit.core package imports
from voteit.core.models.content_utility import ContentUtility
from voteit.core.models.interfaces import IContentUtility
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.security import groupfinder


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
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
    
    #Include content types and their utility IContentUtility
    config.registry.registerUtility(ContentUtility(), IContentUtility)
    
    content_types = settings.get('content_types')
    if content_types is None:
        raise ValueError("content_types must exist in application configuration."
                         "It should point to includable modules, like voteit.core.models.meeting")
    for content_type in content_types.strip().splitlines():
        config.include(content_type)
    
    #include specified poll plugins
    poll_plugins = settings.get('poll_plugins')

    if poll_plugins is not None:
        for poll_plugin in poll_plugins.strip().splitlines():
            config.include(poll_plugin)

    # load workflow
    # FIXME: use package-relative dotted name insted of absolute path
    xmlconfig.file('src/voteit.core/voteit/core/workflows/meeting.xml', execute=True)
    xmlconfig.file('src/voteit.core/voteit/core/workflows/agenda_item.xml', execute=True)
    xmlconfig.file('src/voteit.core/voteit/core/workflows/proposal.xml', execute=True)
    xmlconfig.file('src/voteit.core/voteit/core/workflows/poll.xml', execute=True)

    return config.make_wsgi_app()


def appmaker(zodb_root):
    if not 'app_root' in zodb_root:
        from voteit.core.bootstrap import bootstrap_voteit
        zodb_root['app_root'] = bootstrap_voteit() #Returns a site root
        import transaction
        transaction.commit()
    return zodb_root['app_root']


def register_poll_plugin(plugin_class, verify=True, registry=None):
    """ Verify and register a Poll Plugin class.
        This is a very expensive method to run - it should only be used during
        startup or testing!
    """
    if verify:
        verifyClass(IPollPlugin, plugin_class)
    if registry is None:
        registry = get_current_registry()
    registry.registerUtility(plugin_class(), IPollPlugin, name = plugin_class.name)


def register_content_info(schema, type_class, update_method=None, verify=True, registry=None):
    if registry is None:
        registry = get_current_registry()
    
    util = registry.getUtility(IContentUtility)
    
    obj = util.create(schema, type_class, update_method=update_method)
    util.add(obj, verify=verify)
    
