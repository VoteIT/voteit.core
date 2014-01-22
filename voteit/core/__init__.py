from pyramid.i18n import TranslationStringFactory
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid_zodbconn import get_connection

from pyramid.config import Configurator
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import AuthTktAuthenticationPolicy


#Must be before all of this packages imports since some other methods might import it
PROJECTNAME = 'voteit.core'
VoteITMF = TranslationStringFactory(PROJECTNAME)
DEFAULT_SETTINGS = {
    'default_locale_name': 'en',
    'default_timezone_name': 'UTC',
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
    from voteit.core.security import groupfinder
    
    #Default pluggable auth
    if 'voteit.default_auth' not in settings:
        settings['voteit.default_auth'] = 'password'

    #Authentication policies
    authn_policy = AuthTktAuthenticationPolicy(secret = read_salt(settings),
                                               callback = groupfinder)
    #FIXME: Note that argument hashalg = 'sha512' isn't valid on Pyramid <1.4 ! We need to check version
    authz_policy = ACLAuthorizationPolicy()
    sessionfact = UnencryptedCookieSessionFactoryConfig('messages')
    return Configurator(settings=settings,
                        authentication_policy=authn_policy,
                        authorization_policy=authz_policy,
                        root_factory=root_factory,
                        session_factory = sessionfact,)

def read_salt(settings):
    """ Read salt file or create a new one if salt_file is specified in the settings. """
    from uuid import uuid4
    from os.path import isfile
    filename = settings.get('salt_file', None)
    if filename is None:
        print "\nUsing random salt which means that all users must reauthenticate on restart."
        print "Please specify a salt file by adding the parameter:\n"
        print "salt_file = <path to file>\n"
        print "in paster ini config and add the salt as the sole contents of the file.\n"
        return str(uuid4())
    if not isfile(filename):
        print "\nCan't find salt file specified in paster ini. Trying to create one..."
        f = open(filename, 'w')
        salt = str(uuid4())
        f.write(salt)
        f.close()
        print "Wrote new salt in: %s" % filename
        return salt
    else:
        f = open(filename, 'r')
        salt = f.read()
        if not salt:
            raise ValueError("Salt file is empty - it needs to contain at least some text. File: %s" % filename)
        f.close()
        return salt

def required_components(config):
    config.include(check_required_settings)
    #Component includes
    config.include('voteit.core.models.user_tags')
    config.include('voteit.core.models.logs')
    config.include('voteit.core.models.date_time_util')
    config.include('voteit.core.models.js_util')
    config.include('voteit.core.js_translations')
    config.include('voteit.core.models.catalog')
    config.include('voteit.core.models.unread')
    config.include('voteit.core.models.flash_messages')
    config.include('voteit.core.models.fanstatic_resources')
    config.include('voteit.core.deform_bindings')
    config.include('voteit.core.models.proposal_ids')
    config.include('voteit.core.plugins.immediate_ap')
    config.include('voteit.core.plugins.invite_only_ap')
    #For password storage
    config.scan('betahaus.pyracont.fields.password')

    cache_ttl_seconds = int(config.registry.settings.get('cache_ttl_seconds', 7200))
    config.add_static_view('static', '%s:static' % PROJECTNAME, cache_max_age = cache_ttl_seconds)
    config.add_static_view('deform', 'deform:static', cache_max_age = cache_ttl_seconds)
    config.add_translation_dirs('deform:locale/',
                                'colander:locale/',
                                '%s:locale/' % PROJECTNAME,)
    config.add_route('register', '/register/{method}')
    for scan_dir in ('models', 'schemas', 'subscribers', 'views'):
        config.scan('%s.%s' % (PROJECTNAME, scan_dir))
    config.include(adjust_default_view_component_order)
    from voteit.core.security import VIEW
    config.set_default_permission(VIEW)
    config.include(register_plugins)
    config.include(register_dynamic_fanstatic_resources)
    config.include(check_required_components)
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

def check_required_settings(config):
    """ Check that at least the required settings are present in the paster.ini file.
        If not, add sane defaults.
    """
    settings = config.registry.settings
    for (k, v) in DEFAULT_SETTINGS.items():
        if k not in settings:
            settings[k] = v
            #FIXME: Logger instead, not stdout!
            print "INFO: No value for '%s' found. Adding '%s' as default value." % (k, v)

def check_required_components(config):
    """ After the process of including components is run, check that something has been included in the required sections.
        For instance poll methods.
    """
    from voteit.core.models.interfaces import IPollPlugin
    from voteit.core.models.interfaces import IProfileImage
    from voteit.core.models.interfaces import IAccessPolicy
    from voteit.core.models.interfaces import IAuthPlugin
    need_at_least_one = {IPollPlugin: ('voteit.core.plugins.majority_poll',),
                         IProfileImage: ('voteit.core.plugins.gravatar_profile_image',),
                         IAccessPolicy: (('voteit.core.plugins.immediate_ap'),
                                         ('voteit.core.plugins.invite_only_ap')),
                         IAuthPlugin: ('voteit.core.plugins.password_auth',)}
    found_adapters = {}
    for adapter_registration in config.registry.registeredAdapters():
        if adapter_registration.provided in need_at_least_one:
            del need_at_least_one[adapter_registration.provided]
    for (k, vals) in need_at_least_one.items():
        #FIXME: Propper logging instead...
        print "INFO: Nothing providing '%s.%s' included in configuration." % (k.__module__, k.__name__)
        for v in vals:
            config.include(v)
            print "Including default: '%s'" % v

def root_factory(request):
    """ Returns root object for each request. See pyramid docs. """
    conn = get_connection(request)
    return appmaker(conn.root())

def appmaker(zodb_root):
    """ This determines the root object for each request. If no site root exists,
        this function will run bootstrap_voteit and create one.
        Read more about traversal in the Pyramid docs.
        
        The funny looking try / except here is to bootstrap the site in case it hasn't been bootstrapped.
        This is faster than using an if statement.
    """
    try:
        return zodb_root['app_root']
    except KeyError:
        from voteit.core.bootstrap import bootstrap_voteit
        zodb_root['app_root'] = bootstrap_voteit() #Returns a site root
        import transaction
        transaction.commit()
        #Set intitial version of database
        from repoze.evolution import ZODBEvolutionManager
        from voteit.core.evolve import VERSION
        manager = ZODBEvolutionManager(zodb_root['app_root'], evolve_packagename='voteit.core.evolve', sw_version=VERSION)
        manager.set_db_version(VERSION)
        manager.transaction.commit()
        return zodb_root['app_root']

def adjust_view_component_order(config):
    """ Set the default order of view components. """
    from betahaus.viewcomponent.interfaces import IViewGroup
    prefix = "vieworder."
    lprefix = len(prefix)
    for (k, v) in config.registry.settings.items():
        if k.startswith(prefix):
            name = k[lprefix:]
            util = config.registry.getUtility(IViewGroup, name = name)
            util.order = v.strip().splitlines()

def adjust_default_view_component_order(config):
    """ Adjust component order if something is specified in the paster.ini file. """
    from betahaus.viewcomponent.interfaces import IViewGroup
    from voteit.core.view_component_order import DEFAULT_VC_ORDER
    for (name, items) in DEFAULT_VC_ORDER:
        util = config.registry.getUtility(IViewGroup, name = name)
        util.order = items

def register_dynamic_fanstatic_resources(config):
    from voteit.core.models.interfaces import IFanstaticResources
    from voteit.core.fanstaticlib import DEFAULT_FANSTATIC_RESOURCES
    util = config.registry.getUtility(IFanstaticResources)
    for res in DEFAULT_FANSTATIC_RESOURCES:
        util.add(*res)

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
