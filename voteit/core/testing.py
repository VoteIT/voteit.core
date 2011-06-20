from pyramid import testing as pyra_testing

from voteit.core.models.request import VoteITRequestMixin


class DummyRequestWithVoteIT(pyra_testing.DummyRequest, VoteITRequestMixin):
    pass

