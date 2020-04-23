from pyramid.renderers import render
from pyramid.response import Response
from zope.component import adapter
from zope.interface.declarations import implementer

from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.vote import Vote
from voteit.core import _


CRITERIA_FAILED = False
CRITERIA_DEPENDS = "condition"  # Depends on conditions in the outcome
CRITERIA_SUCCESS = True

CRITERIA_ICONS = {
    CRITERIA_SUCCESS: "glyphicon glyphicon-ok text-success",
    CRITERIA_DEPENDS: "glyphicon glyphicon-question-sign text-warning",
    CRITERIA_FAILED: "glyphicon glyphicon-remove text-danger",
}


class Criteria(object):
    status = None
    title = None
    help = None  # Longer explanation of what the criterion does.
    comment = None  # "Only under these cricumstances..." for instance
    icon = None

    def __init__(self, status, title=None, help=None, comment=None):
        assert status in (CRITERIA_FAILED, CRITERIA_SUCCESS, CRITERIA_DEPENDS)
        self.status = status
        if title:
            self.title = title
        if help:
            self.help = help
        if comment:
            self.comment = comment
        self.icon = CRITERIA_ICONS[status]


# Default important criteria you might want to use
class MajorityWinner(Criteria):
    title = _("Majority winner")
    help = _(
        "criteria_mw_help",
        default="A majority (more than 50%) must prefer this, otherwise it shouldn't be able to win.",
    )


class MajorityLooser(Criteria):
    title = _("Majority looser")
    help = _(
        "criteria_ml_help",
        default="If a majority of voters do not want this, it shouldn't be able to win.",
    )


class MutialMajority(Criteria):
    title = _("Mutial majority")
    help = _(
        "criteria_mm_help",
        default="If there's a subset of candidates where every voter prefer "
        "other candidates within the subset and the subset itself has a majority, "
        "then the winner must come from the subset. "
        "Example: Alice (apple with 30% vote share) and "
        "Granny Smith (apple with 30% vote share) goes against Navelina (orange with 40%). "
        "All Alice/GS fans prefer the other apple over the orange, so one of the apples should win.",
    )


class CondorcetWinner(Criteria):
    title = _("Condorcet winner")
    help = _(
        "criteria_cw_help",
        default="The winner must beat every other candidate in a pairwise comparison.",
    )


class CondorcetLooser(Criteria):
    title = _("Condorcet looser")
    help = _(
        "criteria_cl_help",
        default="The looser must loose against every other candidate in a pairwise comparison.",
    )


class CloneProof(Criteria):
    title = _("Clone proof")
    help = _(
        "criteria_cp_help",
        default="The winner must not change due to strategic nomination, for instance that a similar candidate runs.",
    )


class Proportional(Criteria):
    title = _("Proportional result")
    help = _(
        "criteria_p_help",
        default="The result should reflect the user base as a whole, for instance: "
                "If n% of the electorate support a particular political party as their favorite, "
                "then roughly n% of seats will be won by that party. "
                "Applies to multiple winner methods.",
    )


@implementer(IPollPlugin)
@adapter(IPoll)
class PollPlugin(object):
    """ Base class for poll plugins. Subclass this to make your own.
        It's not usable by itself, since it doesn't implement the required interfaces.
        See :mod:`voteit.core.models.interfaces.IPollPlugin` for documentation.
    """

    @property
    def name(self):
        raise NotImplementedError("Must be provided by subclass")  # pragma : no cover

    @property
    def title(self):
        raise NotImplementedError("Must be provided by subclass")  # pragma : no cover

    description = ""
    selectable = True
    long_description_tpl = None
    # Use this to determine if poll is applicable
    # Position in listing, lower number is better
    priority = 100
    # Number of proposals restrictions
    proposals_min = None  # int
    proposals_max = None  # int
    multiple_winners = None  # bool
    recommended_for = None  # string
    criteria = []  # List containing Criteria instances
    CRITERIA_FAILED = CRITERIA_FAILED
    CRITERIA_DEPENDS = CRITERIA_DEPENDS
    CRITERIA_SUCCESS = CRITERIA_SUCCESS
    CRITERIA_ICONS = CRITERIA_ICONS

    def __init__(self, context):
        self.context = context

    @classmethod
    def long_description(cls, request):
        """ Optional method to render a longer description with html for the select form.
        """
        if cls.long_description_tpl is not None:
            return render(cls.long_description_tpl, {"factory": cls}, request=request)

    @classmethod
    def get_criteria(cls):
        for (k, title) in cls.CRITERIA:
            criteria = getattr(cls, k, None)
            if isinstance(criteria, Criteria):
                yield (title, criteria)

    def get_vote_schema(self):
        """ Return the schema of how a vote should be structured.
            This is used to render a voting form.
        """
        raise NotImplementedError("Must be provided by subclass")  # pragma : no cover

    def get_vote_class(self):
        """ Get the vote class to use for this poll. Normally it's the
            voteit.core.models.vote.Vote class.
        """
        return Vote  # pragma : no cover

    def get_settings_schema(self):
        """ Get an instance of the schema used to render a form for editing settings.
            If this is None, this poll method doesn't have any settings.
        """
        return None  # pragma : no cover

    def handle_start(self, request):
        """ Optional method to adjust things when poll starts, or check sanity of poll settings.
            Raises HTTPForbidden on errors, and BadPollMethodError for things that could be bypassed
            if you want to have a poll that doesn't make any sense.
        """
        pass

    def handle_close(self):
        """ Handle closing of the poll.
        """
        raise NotImplementedError("Must be provided by subclass")  # pragma : no cover

    def render_result(self, view):
        """ Return rendered html with result display. Called by the poll view
            when the poll has finished.
        """
        raise NotImplementedError("Must be provided by subclass")  # pragma : no cover

    def change_states_of(self):
        """ This gets called when a poll has finished.
            It returns a dictionary with proposal uid as key and new state as value.
            Like: {'<uid>':'approved', '<uid>', 'denied'}
            It's not required to do, but if it isn't done, the proposals won't change state
            and you have to do it manually.
            It's not required to return anything.
        """
        return {}  # pragma : no cover

    def render_raw_data(self):
        """ Return rendered html with raw data from this poll.
            It should consist of ballot information.
            It can either be anonymous, or actually show the userids of the ones
            that voted. That's just a matter of taste.
            The point with this view is to enable others to run
            a poll to verify the result.
            
            The method needs to return an instance of either:
            - pyramid.renderers.render
            - pyramid.response.Response
        """
        return Response(unicode(self.context.ballots))
