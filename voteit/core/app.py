""" App configuration and loading.
    - Use imports carefully. It might not be clear when this file is run,
      so import things from the voteit.core package in each method rather than globally.
    - Don't put anything here that will run after application configuration.
"""
import os, fnmatch

from pyramid.events import ApplicationCreated
from pyramid.events import subscriber
from pyramid.config import Configurator
from zope.interface.verify import verifyClass

from voteit.core.models.interfaces import ICatalogMetadata
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.interfaces import IDateTimeUtil


def register_poll_plugins(config):
    """ Register poll plugins configured in the paster .ini file.
    """
    
    poll_plugins = config.registry.settings.get('poll_plugins')
    if poll_plugins is not None:
        for poll_plugin in poll_plugins.strip().splitlines():
            config.include(poll_plugin)
    else:
        raise ValueError("At least one poll plugin must be used")


def register_catalog_metadata_adapter(config):
    from voteit.core.models.catalog import CatalogMetadata
    config.registry.registerAdapter(CatalogMetadata, (ICatalogMetadataEnabled,), ICatalogMetadata)


def add_date_time_util(config, locale=None, timezone_name=None):
    """ """
    from voteit.core.models.date_time_util import DateTimeUtil
    
    if locale is None:
        locale = config.registry.settings.get('default_locale_name')

    if timezone_name is None:
        timezone_name = config.registry.settings.get('default_timezone_name')

    util = DateTimeUtil(locale, timezone_name)
    config.registry.registerUtility(util, IDateTimeUtil)


def include_zcml(config):
    config.include('pyramid_zcml')
    config.load_zcml('voteit.core:configure.zcml')
    config.commit()


def register_poll_plugin(plugin_class, verify=True, registry=None):
    """ Verify and register a Poll Plugin class.
        This is a very expensive method to run - it should only be used during
        startup or testing!
    """
    if verify:
        verifyClass(IPollPlugin, plugin_class)
    if registry is None:
        raise ValueError("Missing required keyword argument registry")
    registry.registerAdapter(plugin_class, (IPoll,), IPollPlugin, plugin_class.name)


@subscriber(ApplicationCreated)
def post_application_config(event):
    """ The zope.component registry must be global if we want to hook components from
        non-Pyramid packages. This stage ensures that zopes getSiteManager method
        will actually return the VoteIT registry rather than something else.
    """
    config = Configurator(registry=event.app.registry)
    include_zcml(config)
