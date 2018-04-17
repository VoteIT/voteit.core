from pyramid.config import Configurator
from pyramid.interfaces import IApplicationCreated


def include_zcml(config):
    """ Include ZCML configuration. """
    config.include('pyramid_zcml')
    config.load_zcml('voteit.core:configure.zcml')
    config.commit()


def post_application_config(event):
    """ The zope.component registry must be global if we want to hook components from
        non-Pyramid packages. This stage ensures that zopes getSiteManager method
        will actually return the VoteIT registry rather than something else.
    """
    config = Configurator(registry=event.app.registry)
    include_zcml(config)


def includeme(config):
    config.add_subscriber(post_application_config, IApplicationCreated)
