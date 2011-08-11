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
from zope.component import getUtility

from sqlalchemy import create_engine
from zope.sqlalchemy import ZopeTransactionExtension

from voteit.core.models.interfaces import ICatalogMetadata
from voteit.core.models.interfaces import IContentUtility
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.interfaces import IHelpUtil
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.interfaces import ISQLSession
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


def register_content_types(config):
    """ Include content types and their utility IContentUtility """
    from voteit.core.models.content_utility import ContentUtility
    
    config.registry.registerUtility(ContentUtility(), IContentUtility)
    
    content_types = config.registry.settings.get('content_types')
    if content_types is None:
        raise ValueError("content_types must exist in application configuration."
                         "It should point to includable modules, like voteit.core.models.meeting")
    
    cts = [x.strip() for x in content_types.strip().splitlines()]
    for content_type in cts:
        config.include(content_type)


def register_catalog_metadata_adapter(config):
    from voteit.core.models.catalog import CatalogMetadata
    config.registry.registerAdapter(CatalogMetadata, (ICatalogMetadataEnabled,), ICatalogMetadata)


def add_sql_session_util(config, sqlite_file=None):
    settings = config.registry.settings

    if sqlite_file is None:
        sqlite_file = settings.get('sqlite_file')
        if sqlite_file is None:
            raise ValueError("""
A path to an SQLite db file needs to be specified.
Something like: 'sqlite_file = sqlite:///%(here)s/../var/sqlite.db'
added in paster setup. (Either development.ini or production.ini)

Alternatively, you can pass sqlite_file as an argument to this method.
            """)
    
    engine = create_engine(sqlite_file)

    from voteit.core.models.sql_session import SQLSession
    util = SQLSession(engine)
    config.registry.registerUtility(util, ISQLSession)

def add_date_time_util(config, locale=None, timezone_name=None):
    """ """
    from voteit.core.models.date_time_util import DateTimeUtil
    
    if locale is None:
        locale = config.registry.settings.get('default_locale_name')

    if timezone_name is None:
        timezone_name = config.registry.settings.get('default_timezone_name')

    util = DateTimeUtil(locale, timezone_name)
    config.registry.registerUtility(util, IDateTimeUtil)

def add_help_util(config, locale=None):
    from voteit.core.models.help_util import HelpUtil
    
    if locale is None:
        locale = config.registry.settings.get('default_locale_name')
    
    util = HelpUtil(locale)
    config.registry.registerUtility(util, IHelpUtil)


def populate_sql_database(config):
    from voteit.core import RDB_Base
    
    sql_util = config.registry.getUtility(ISQLSession)
    
    #Touch all modules that are SQL-based
    from voteit.core.models.expression import Expression
    from voteit.core.models.log import logs_tags
    from voteit.core.models.log import Log
    from voteit.core.models.log import LogTag
    from voteit.core.models.unread import Unread
    from voteit.core.models.message import messages_tags
    from voteit.core.models.message import Message
    from voteit.core.models.message import MessageTag
    
    #Create tables
    RDB_Base.metadata.create_all(sql_util.engine)
    
    session = sql_util()


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


def register_content_info(schema, type_class, verify=True, registry=None):
    if registry is None:
        raise ValueError("Missing required keyword argument registry")
    
    util = registry.getUtility(IContentUtility)
    
    obj = util.create(schema, type_class)
    util.add(obj, verify=verify)



@subscriber(ApplicationCreated)
def post_application_config(event):
    """ The zope.component registry must be global if we want to hook components from
        non-Pyramid packages. This stage ensures that zopes getSiteManager method
        will actually return the VoteIT registry rather than something else.
    """
    config = Configurator(registry=event.app.registry)
    include_zcml(config)
    
    # read help files
    # get path of this file
    PROJECTROOT = os.path.dirname( __file__ )
    help_util = getUtility(IHelpUtil)
    # get help files path
    helpdir = os.path.join(PROJECTROOT, 'help')
    # loop through locale directories
    for path, dirs, files in os.walk(helpdir):
        for name in dirs:
            dir = os.path.join(path, name)
            # loop through html files in locale directories
            for file in fnmatch.filter(os.listdir(dir), '*.html'):
                # get the name of the file without extension
                id = os.path.splitext(file)[0]
                # add file to HelpUtil
                help_util.add_help_file(id, os.path.join(dir, file))
    

