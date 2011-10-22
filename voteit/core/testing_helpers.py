from transaction import commit
from pyramid_zodbconn import db_from_uri
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid import testing

from voteit.core.bootstrap import bootstrap_voteit
from voteit.core.security import ROLE_VOTER


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
    config.scan('voteit.core.models.user')
    config.scan('voteit.core.models.users')
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
    #unrestricted_wf_transition_to(meeting, 'ongoing')
    meeting.set_workflow_state(request, 'ongoing')
    
    ai = meeting['ai'] = AgendaItem()
    ai['prop1'] = Proposal()
    ai['prop2'] = Proposal()
    #unrestricted_wf_transition_to(ai, 'upcoming')
    #unrestricted_wf_transition_to(ai, 'ongoing')
    ai.set_workflow_state(request, 'upcoming')
    ai.set_workflow_state(request, 'ongoing')
    ai['poll'] = Poll()
    poll = ai['poll']
    poll.set_field_value('proposals', set([ai['prop1'].uid, ai['prop2'].uid]))
    #unrestricted_wf_transition_to(poll, 'upcoming')
    poll.set_workflow_state(request, 'upcoming')

    register_security_policies(config)

    return root