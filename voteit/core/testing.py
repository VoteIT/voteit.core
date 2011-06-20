from pyramid import testing as pyra_testing

from voteit.core.models.request import VoteITRequestMixin


class DummyRequestWithVoteIT(pyra_testing.DummyRequest, VoteITRequestMixin):
    """ Same as DummyRequest, but it can have a real context set.
    """
    
    def __init__(self, params=None, environ=None, headers=None, path='/',
                 cookies=None, post=None, context=None, **kw):
        super(DummyRequestWithVoteIT, self).__init__(params=None, environ=None, headers=None, path='/',
                                                     cookies=None, post=None, **kw)
        self.context = context
