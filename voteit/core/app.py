""" App configuration and loading.
    - Use imports carefully. It might not be clear when this file is run,
      so import things from the voteit.core package in each method rather than globally.
    - Don't put anything here that will run after application configuration.
"""

from pyramid.events import ApplicationCreated
from pyramid.events import subscriber
from pyramid.config import Configurator
from zope.interface.verify import verifyClass

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension

from voteit.core.models.interfaces import IContentUtility
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin


def register_request_factory(config):
    from voteit.core.models.request import VoteITRequestFactory
    config.set_request_factory(VoteITRequestFactory)


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
    for content_type in content_types.strip().splitlines():
        config.include(content_type)


def init_sql_database(settings):
    from voteit.core import RDB_Base
    
    sqlite_file = settings.get('sqlite_file')
    if sqlite_file is None:
        raise ValueError("""
        A path to an SQLite db file needs to be specified.
        Something like: 'sqlite_file = sqlite:///%(here)s/../var/sqlite.db'
        added in paster setup. (Either development.ini or production.ini)
        """)

    settings['rdb_engine'] = create_engine(sqlite_file)
    settings['rdb_session_factory'] = sessionmaker(bind=settings['rdb_engine'],
                                                   extension=ZopeTransactionExtension())

    #Touch all modules that are SQL-based
    from voteit.core.models.expression import Expression
    from voteit.core.models.message import Message
    from voteit.core.models.message import MessageRead
    from voteit.core.models.log import log_tags
    from voteit.core.models.log import Log
    from voteit.core.models.log import Tag
    from voteit.core.models.unread import Unread
    
    #Create tables
    RDB_Base.metadata.create_all(settings['rdb_engine'])


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
