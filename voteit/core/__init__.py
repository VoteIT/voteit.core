import logging

from arche import base_config
from pyramid.i18n import TranslationStringFactory


log = logging.getLogger(__name__)


#Must be before all of this packages imports since some other methods might import it
PROJECTNAME = 'voteit.core'
_ = VoteITMF = TranslationStringFactory(PROJECTNAME)
DEFAULT_SETTINGS = {
    'voteit.gravatar_default': 'mm',
    'voteit.default_profile_picture': '/voteit_core_static/images/default_user.png',
    'pyramid_deform.template_search_path': 'voteit.core:templates/widgets arche:templates/deform',
    'arche.hash_method': 'voteit.core.security.get_sha_password',
    'arche.favicon': 'voteit.core:static/favicon.ico',
    'arche.actionbar': 'voteit.core.views.render_actionbar',
}

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
        If you don't want to start the VoteIT app from this method,
        be sure to include the same things at least.
    """
    check_required_settings(settings)
    config = base_config(**settings)
    config.include(required_components)
    config.hook_zca()
    return config.make_wsgi_app()

def required_components(config):
    #Other includes
    config.include('pyramid_zodbconn')
    config.include('pyramid_tm')
    config.include('pyramid_chameleon')
    config.include('pyramid_deform')
    config.include('deform_autoneed')
    config.include('betahaus.viewcomponent')
    #Arche
    cache_max_age = int(config.registry.settings.get('arche.cache_max_age', 60*60*24))
    config.add_static_view('static', 'arche:static', cache_max_age = cache_max_age)
    config.include('arche') #Must be included first to adjust settings for other packages!
    config.include('arche_usertags')
    #Include all major components
    config.include('voteit.core.models')
    config.include('voteit.core.fanstaticlib')
    config.include('voteit.core.security')
    config.include('voteit.core.subscribers')
    config.include('voteit.core.views')
    config.include('voteit.core.schemas')
    config.include('voteit.core.workflows')
    #Plugins and minor dependent components
    config.include('voteit.core.helpers')
    config.include('voteit.core.plugins.immediate_ap')
    config.include('voteit.core.plugins.invite_only_ap')
    config.add_portlet_slot('left_fixed', title=_("Fixed left nav"), layout='vertical')
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

def check_required_settings(settings):
    """ Check that at least the required settings are present in the paster.ini file.
        If not, add sane defaults.
        This function may fire several times
    """
    for (k, v) in DEFAULT_SETTINGS.items():
        if k not in settings:
            settings[k] = v
            log.debug("Required value '%s' not found. Adding '%s' as default value.", k, v)

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
    for adapter_registration in config.registry.registeredAdapters():
        if adapter_registration.provided in need_at_least_one:
            del need_at_least_one[adapter_registration.provided]
    for (k, vals) in need_at_least_one.items():
        log.warn("Nothing providing '%s.%s' included in configuration." % (k.__module__, k.__name__))
        for v in vals:
            config.include(v)
            log.info("Including default: '%s'" % v)

def includeme(config):
    """ Called when voteit.core is used as a component of another application.
        It should load its default components, but not make too much assumptions.
        This is also a good plugin point for other applications integration tests.
        It's important that hook_zca is run in the calling package, otherwise
        workflows won't work.
        Compare with startup in main.
        Note that you still need to add all the things added in the default_configurator method.
    """
    check_required_settings(config.registry.settings)
    config.include(required_components)
