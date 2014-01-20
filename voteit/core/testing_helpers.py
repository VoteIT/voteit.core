from transaction import commit
from pyramid_zodbconn import db_from_uri
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid import testing
from pyramid_mailer.interfaces import IMailer

from voteit.core.bootstrap import bootstrap_voteit
from voteit.core.security import ROLE_VOTER


class PrintingMailer(object):
    """
    Dummy mailing instance. Simply prints all messages directly instead of handling them.
    Good for avoiding mailing users when you want to test things locally.
    """

    def send(self, message):    
        """
        Send, but really print content of message
        """
        
        print "From: %s " % message.sender
        print "Subject: %s" % message.subject
        print "To: %s" % ", ".join(message.recipients)
        print "======================================"
        print message.html
        print message.body

    send_to_queue = send_immediately = send


def create_full_app_config():
    """ This is a full config including everything.
        Only use it for high level tests since it will take time to load it.
    """
    from voteit.core import default_configurator
    from voteit.core import required_components
    settings = full_app_settings()
    config = default_configurator(settings)
    config.include(required_components)
    config.hook_zca()
    return config


def full_app_settings():
    """ Settings suitable for testing. It will use a database with memory storage
        so no changes will ever be permanent.
    """
    return {
        #Pyramid defaults
        "pyramid.debug_templates": "true",
        "pyramid.includes": """
            pyramid_zodbconn
            pyramid_tm
            pyramid_mailer.testing
        """.strip(),
        #Transaction manager config for package: pyramid_tm
        "tm.attempts": "1",
        "tm.commit_veto": "pyramid_tm.default_commit_veto",
        #ZODB config for package: pyramid_zodbconn
        "zodbconn.uri": "memory://testingstorage",
        #VoteIT settings
        "default_locale_name": "en",
        "default_timezone_name": "Europe/Stockholm",
        "tkt_secret": "testing",
        "cache_ttl_seconds": "3600"
    }


def printing_mailer(config):
    """ Include this to use the printing mailer."""
    print "\nWARNING! Using printing mailer - no mail will be sent!\n"
    mailer = PrintingMailer()
    config.registry.registerUtility(mailer, IMailer)


def dummy_zodb_root(config):
    """ Returns a bootstrapped root object that has been attached to
        a ZODB database that only exist in memory. It will behave
        the same way as a database that would be stored permanently.
    """

    db = db_from_uri('memory://')
    conn = db.open()
    zodb_root = conn.root()
    zodb_root['app_root'] = bootstrap_and_fixture(config)
    commit()
    return zodb_root['app_root']


def bootstrap_and_fixture(config):
    config.include('pyramid_zcml')
    config.load_zcml('voteit.core:configure.zcml')
    config.scan('voteit.core.models.site')
    config.scan('voteit.core.models.agenda_templates')
    config.scan('voteit.core.models.user')
    config.scan('voteit.core.models.users')
    config.include('voteit.core.models.fanstatic_resources')
    config.scan('betahaus.pyracont.fields.password')
    return bootstrap_voteit(echo=False)


def register_security_policies(config):
    from voteit.core.security import groupfinder
    authn_policy = AuthTktAuthenticationPolicy(secret='secret',
                                               callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()
    config.setup_registry(authorization_policy=authz_policy, authentication_policy=authn_policy)


def register_workflows(config):
    config.include('pyramid_zcml')
    config.load_zcml('voteit.core:configure.zcml')


def register_catalog(config):
    """ Register minimal components needed to enable the catalog in testing. """
    config.include('voteit.core.models.catalog')
    config.include('voteit.core.models.unread')
    config.include('voteit.core.models.user_tags')
    config.scan('voteit.core.subscribers.catalog')
    #Without order, sorting in that index will remove content rather than show it. Very weird.
    config.scan('voteit.core.subscribers.agenda_item')
    


def active_poll_fixture(config):
    """ This method sets up a site the way it will be when a poll is ready to start
        with admin as voter.
        You can use this if you want a fixture for your poll plugin tests
    """
    root = bootstrap_and_fixture(config)
    from voteit.core.models.poll import Poll
    from voteit.core.models.meeting import Meeting
    from voteit.core.security import unrestricted_wf_transition_to
    from voteit.core.models.agenda_item import AgendaItem
    from voteit.core.models.proposal import Proposal

    request = testing.DummyRequest()
    config = testing.setUp(request = request, registry = config.registry)

    config.include('pyramid_mailer.testing')
    config.scan('voteit.core.subscribers.poll')
    config.scan('voteit.core.models.meeting')
    root['users']['admin'].set_field_value('email', 'this@that.com')
    meeting = root['meeting'] = Meeting()
    meeting.add_groups('admin', [ROLE_VOTER])
    meeting.set_workflow_state(request, 'ongoing')
    
    ai = meeting['ai'] = AgendaItem()
    ai['prop1'] = Proposal(title = u"Proposal 1")
    ai['prop2'] = Proposal(title = u"Proposal 2")
    ai.set_workflow_state(request, 'upcoming')
    ai.set_workflow_state(request, 'ongoing')
    ai['poll'] = Poll(title = 'A poll')
    poll = ai['poll']
    poll.set_field_value('proposals', set([ai['prop1'].uid, ai['prop2'].uid]))
    poll.set_workflow_state(request, 'upcoming')
    register_security_policies(config)
    return root
