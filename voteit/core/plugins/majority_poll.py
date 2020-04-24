from __future__ import unicode_literals

from decimal import Decimal
from operator import itemgetter

import colander
import deform
from pyramid.httpexceptions import HTTPForbidden
from pyramid.renderers import render
from pyramid.response import Response

from voteit.core.exceptions import BadPollMethodError
from voteit.core.models.poll_plugin import PollPlugin
from voteit.core import _


class MajorityPollPlugin(PollPlugin):
    """ Majority poll plugin. An example of how plugins work. """

    name = "majority_poll"
    title = _("Majority Poll")
    description = _(
        "majority_poll_desc",
        default="A standard majority poll with radio buttons. "
        "Simple graphs will display the result. ",
    )
    multiple_winners = False
    proposals_min = 2
    proposals_max = 2
    recommended_for = _("Simple choices between 2 proposals")
    # Position in listing, lower number is better
    priority = 5

    def get_settings_schema(self):
        """ Get an instance of the schema used to render a form for editing settings.
            This form doesn't have any settings, so the schema is empty.
        """
        return None

    def get_vote_schema(self):
        """ Get an instance of the schema that this poll uses.
        """
        proposals = self.context.get_proposal_objects()
        # Choices should be something iterable with the contents [(UID for proposal, Title of proposal), <etc...>, ]
        choices = set()
        for prop in proposals:
            title = "#%s - %s" % (prop.get_field_value("aid"), prop.text)
            choices.add((prop.uid, title))
        poll_wf_state = self.context.get_workflow_state()
        if poll_wf_state == "ongoing":
            proposal_title = _("Vote for one")
        else:
            proposal_title = _("You can't change your vote now.")

        class Schema(colander.Schema):
            widget = deform.widget.FormWidget(
                template="form_modal", readonly_template="readonly/form_modal"
            )
            proposal = colander.SchemaNode(
                colander.String(),
                validator=colander.OneOf([x[0] for x in choices]),
                widget=deform.widget.RadioChoiceWidget(values=choices),
                title=proposal_title,
                description="",
            )

        return Schema()

    def handle_start(self, request):
        prop_count = len(self.context.proposals)
        if prop_count == 1:
            raise HTTPForbidden(_("Only one proposal selected"))
        if prop_count > 2:
            msg = _(
                "majority_poll_too_many_props",
                default="Majority polls with more than 2 proposals may not yield a complete "
                "result or will force tactical voting.",
            )
            raise BadPollMethodError(
                _(msg),
                self.context,
                request,
                recommendation=_("Use Schulze method instead"),
            )

    def handle_close(self):
        """ Get the calculated result of this ballot.
            We'll update the ballots with percentage and simply return them.
            The result should look something like this:
            [{'count': 1, 'percentage': '33.33333%', num: 33.33333, ballot': {'proposal': 'af4aa2bc-1ebb-43e1-811b-88ec6ed0e2d1'}}, <etc...>, ]
        """
        ballots = self.context.ballots
        results = []
        if ballots:
            total_votes = sum([x[1] for x in ballots])
            for (uid, count) in ballots:
                result = {}
                num = Decimal(count) / total_votes
                result["num"] = num
                result["uid"] = uid
                result["count"] = count
                results.append(result)
        self.context.poll_result = tuple(
            sorted(results, key=itemgetter("num"), reverse=True)
        )

    def render_result(self, view):
        votes = [x["uid"]["proposal"] for x in self.context.poll_result]
        novotes = set(self.context.proposal_uids) - set(votes)
        translate = view.request.localizer.translate
        vote_singular = translate(_("vote_singular", default="Vote"))
        vote_plural = translate(_("vote_plural", default="Votes"))

        def _vote_text(count):
            return view.request.localizer.pluralize(vote_singular, vote_plural, count)

        results = []
        # Adjust result layout
        for res in tuple(self.context.poll_result):
            results.append(
                {
                    "uid": res["uid"]["proposal"],
                    "count": res["count"],
                    "num": res["num"],
                    "perc": int(round(res["num"] * 100, 0)),
                }
            )
        for uid in novotes:
            results.append({"uid": uid, "count": 0, "num": 0, "perc": 0})
        response = {}
        response["results"] = results
        # response['novotes'] = novotes
        response["vote_text"] = _vote_text
        response["total"] = sum([x[1] for x in self.context.ballots])
        proposals = {}
        for prop in self.context.get_proposal_objects():
            proposals[prop.uid] = prop
        response["proposals"] = proposals
        return render("templates/majority_poll.pt", response, request=view.request)

    def change_states_of(self):
        """ This gets called when a poll has finished.
            It returns a dictionary with proposal uid as key and new state as value.
            Like: {'<uid>':'approved', '<uid>', 'denied'}
        """
        result = {}
        poll_result = sorted(
            self.context.poll_result, key=itemgetter("num"), reverse=True
        )
        # if no result return empty dictionary
        if len(poll_result) == 0:
            return {}
        # check if it's result is undesided
        if len(poll_result) > 1:
            if poll_result[0]["num"] == poll_result[1]["num"]:
                return {}
        # set first as approved and the rest as denied
        result[poll_result[0]["uid"]["proposal"]] = "approved"
        for loser in poll_result[1:]:
            result[loser["uid"]["proposal"]] = "denied"
        # set the proposals without votes as denied
        for proposal in self.context.get_proposal_objects():
            if proposal.uid not in result:
                result[proposal.uid] = "denied"
        return result

    def render_raw_data(self):
        return Response(unicode(self.context.ballots))


def includeme(config):
    """ Include majority poll as a usable method.
    """
    config.registry.registerAdapter(MajorityPollPlugin, name=MajorityPollPlugin.name)
