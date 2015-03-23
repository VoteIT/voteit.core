import logging

from arche import root_factory
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from pyramid_zodbconn import get_connection


log = logging.getLogger(__name__)


#Must be before all of this packages imports since some other methods might import it
PROJECTNAME = 'voteit.core'
_ = VoteITMF = TranslationStringFactory(PROJECTNAME)
DEFAULT_SETTINGS = {
    'voteit.gravatar_default': 'mm',
    'voteit.default_profile_picture': '/static/images/default_user.png',
    'pyramid_deform.template_search_path': 'voteit.core:views/templates/widgets arche:templates/deform',
    'arche.hash_method': 'voteit.core.security.get_sha_password',
    'arche.favicon': 'voteit.core:static/favicon.ico',
}

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
        If you don't want to start the VoteIT app from this method,
        be sure to include the same things at least.
    """
    config = default_configurator(settings)
    config.include(required_components)
    config.hook_zca()
    return config.make_wsgi_app()

def default_configurator(settings):
    from arche.security import groupfinder
    from arche import read_salt
    authn_policy = AuthTktAuthenticationPolicy(hashalg='sha512',
                                               secret = read_salt(settings),
                                               callback = groupfinder)
    authz_policy = ACLAuthorizationPolicy()
    return Configurator(settings=settings,
                        authentication_policy=authn_policy,
                        authorization_policy=authz_policy,
                        root_factory=root_factory,)

def required_components(config):
    config.include(check_required_settings)
    #Other includes
    config.include('pyramid_zodbconn')
    config.include('pyramid_tm')
    config.include('pyramid_chameleon')
    config.include('pyramid_deform')
    config.include('pyramid_beaker')
    config.include('deform_autoneed')
    #Arche
    cache_max_age = int(config.registry.settings.get('arche.cache_max_age', 60*60*24))
    config.add_static_view('static', 'arche:static', cache_max_age = cache_max_age)
    config.include('arche') #Must be included first to adjust settings for other packages!
    
    #Include all major components
    config.include('voteit.core.models')
    config.include('voteit.core.fanstaticlib')
    config.include('voteit.core.security')
    config.include('voteit.core.subscribers')
    config.include('voteit.core.views')
    config.include('voteit.core.schemas')
    #Plugins and minor dependent components
    config.include('voteit.core.helpers')
    config.include('voteit.core.js_translations')
    config.include('voteit.core.plugins.immediate_ap')
    config.include('voteit.core.plugins.invite_only_ap')
    config.include('voteit.core.portlets')

    config.add_static_view('voteit_core_static', '%s:static' % PROJECTNAME, cache_max_age = cache_max_age)
    config.add_translation_dirs('%s:locale/' % PROJECTNAME,)
    #Include all subcomponents
    from voteit.core.security import VIEW
    config.set_default_permission(VIEW)    
    config.include(register_plugins)
    config.include(check_required_components)
    config.override_asset(to_override='arche:templates/',
                          override_with='voteit.core:templates/overrides/')

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

def check_required_settings(config):
    """ Check that at least the required settings are present in the paster.ini file.
        If not, add sane defaults.
    """
    settings = config.registry.settings
    for (k, v) in DEFAULT_SETTINGS.items():
        if k not in settings:
            settings[k] = v
            log.warn("Required value '%s' not found. Adding '%s' as default value." % (k, v))

def check_required_components(config):
    """ After the process of including components is run, check that something has been included in the required sections.
        For instance poll methods.
    """
    from voteit.core.models.interfaces import IPollPlugin
    from voteit.core.models.interfaces import IProfileImage
    from voteit.core.models.interfaces import IAccessPolicy
    need_at_least_one = {IPollPlugin: ('voteit.core.plugins.majority_poll',),
                         IProfileImage: ('voteit.core.plugins.gravatar_profile_image',),
                         IAccessPolicy: (('voteit.core.plugins.immediate_ap'),
                                         ('voteit.core.plugins.invite_only_ap')),}
    found_adapters = {}
    for adapter_registration in config.registry.registeredAdapters():
        if adapter_registration.provided in need_at_least_one:
            del need_at_least_one[adapter_registration.provided]
    for (k, vals) in need_at_least_one.items():
        log.warn("Nothing providing '%s.%s' included in configuration." % (k.__module__, k.__name__))
        for v in vals:
            config.include(v)
            log.info("Including default: '%s'" % v)

# def root_factory(request):
#     """ Returns root object for each request. See pyramid docs. """
#     conn = get_connection(request)
#     return appmaker(conn.root())
# 
# def appmaker(zodb_root):
#     """ This determines the root object for each request. If no site root exists,
#         this function will run bootstrap_voteit and create one.
#         Read more about traversal in the Pyramid docs.
#         
#         The funny looking try / except here is to bootstrap the site in case it hasn't been bootstrapped.
#         This is faster than using an if statement.
#     """
#     try:
#         return zodb_root['app_root']
#     except KeyError:
#         from voteit.core.bootstrap import bootstrap_voteit
#         zodb_root['app_root'] = bootstrap_voteit() #Returns a site root
#         import transaction
#         transaction.commit()
#         #Set intitial version of database
#         from repoze.evolution import ZODBEvolutionManager
#         from voteit.core.evolve import VERSION
#         manager = ZODBEvolutionManager(zodb_root['app_root'], evolve_packagename='voteit.core.evolve', sw_version=VERSION)
#         manager.set_db_version(VERSION)
#         manager.transaction.commit()
#         return zodb_root['app_root']

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
