from decimal import Decimal

import colander
import deform
from pyramid.renderers import render
from pyramid.response import Response

from voteit.core.models.poll_plugin import PollPlugin
from voteit.core.models.vote import Vote
from voteit.core import VoteITMF as _


class MajorityPollPlugin(PollPlugin):
    """ Majority poll plugin. An example of how plugins work. """
    
    name = u'majority_poll'
    title = _(u'Majority Poll')
    #FIXME: Description of majority poll
    description = _(u'Description of majority poll')
    
    def get_settings_schema(self):
        """ Get an instance of the schema used to render a form for editing settings.
            This form doesn't have any settings, so the schema is empty.
        """
        return None
    
    def get_vote_schema(self, request=None, api=None):
        """ Get an instance of the schema that this poll uses.
        """
        proposals = self.context.get_proposal_objects()
        
        #Choices should be something iterable with the contents [(UID for proposal, Title of proposal), <etc...>, ]
        choices = set()
        
        for prop in proposals:
            choices.add((prop.uid, prop.title))

        poll_wf_state = self.context.get_workflow_state()
        if poll_wf_state == 'ongoing':
            proposal_title = _(u"Vote for one")
        else:
            proposal_title = _(u"You can't change your vote now.")

        class Schema(colander.Schema):
            proposal = colander.SchemaNode(
                            colander.String(),
                            validator=colander.OneOf([x[0] for x in choices]),
                            widget=deform.widget.RadioChoiceWidget(values=choices),
                            title=proposal_title,
                            description=u'',)

        return Schema()

    def get_vote_class(self):
        return Vote

    def handle_close(self):
        """ Get the calculated result of this ballot.
            We'll update the ballots with percentage and simply return them.
            The result should look something like this:
            [{'count': 1, 'percentage': '33.33333%', num: 33.33333, ballot': {'proposal': u'af4aa2bc-1ebb-43e1-811b-88ec6ed0e2d1'}}, <etc...>, ]
        """
        ballots = self.context.ballots
        results = []
        if ballots:
            total_votes = sum([x[1] for x in ballots])
            for (uid, count) in ballots:
                result = {}
                num = Decimal(count) / total_votes
                result['percentage'] = self._get_percentage(num)
                result['num'] = num
                result['uid'] = uid
                result['count'] = count
                results.append(result)
            
        from operator import itemgetter
        self.context.poll_result = sorted(results, key=itemgetter('num'), reverse=True)

    def _get_percentage(self, num):
        return u"%s%%" % (round(num*100, 1))
        
    def render_result(self, request, api, complete=True):
        votes = [x['uid']['proposal'] for x in self.context.poll_result]
        novotes = self.context.proposal_uids - set(votes)
        
        response = {}
        response['api'] = api
        response['result'] = self.context.poll_result
        response['novotes'] = novotes
        response['get_proposal_by_uid'] = self.context.get_proposal_by_uid
        response['complete'] = complete
        return render('templates/majority_poll.pt', response, request=request)

    def change_states_of(self):
        """ This gets called when a poll has finished.
            It returns a dictionary with proposal uid as key and new state as value.
            Like: {'<uid>':'approved', '<uid>', 'denied'}
        """
        result = {}

        from operator import itemgetter
        poll_result = sorted(self.context.poll_result, key=itemgetter('num'), reverse=True)

        # if no result return empty dictionary
        if len(poll_result) == 0:
            return {}

        # check if it's result is undesided
        if len(poll_result) > 1:
            if poll_result[0]['num'] == poll_result[1]['num']:
                return {}

        # set first as approved and the rest as denied
        result[poll_result[0]['uid']['proposal']] = 'approved'
        for loser in poll_result[1:]:
            result[loser['uid']['proposal']] = 'denied'
            
        # set the proposals without votes as denied
        for proposal in self.context.get_proposal_objects():
            if proposal.uid not in result:
                result[proposal.uid] = 'denied'
        
        return result

    def render_raw_data(self):
        return Response(unicode(self.context.ballots))


def includeme(config):
    """ Include majority poll as a usable method.
    """
    from voteit.core.models.interfaces import IPoll
    from voteit.core.models.interfaces import IPollPlugin
    config.registry.registerAdapter(MajorityPollPlugin, (IPoll,), IPollPlugin, MajorityPollPlugin.name)
