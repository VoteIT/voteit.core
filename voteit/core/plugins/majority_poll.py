import colander
import deform
from pyramid.renderers import render

from voteit.core.models.poll_plugin import PollPlugin
from voteit.core.models.vote import Vote
from voteit.core import register_poll_plugin
from voteit.core import VoteITMF as _


class MajorityPollPlugin(PollPlugin):
    """ Majority poll plugin. An example of how plugins work. """

    name = u'majority_poll'
    title = u'Majority Poll'
    
    def get_settings_schema(self, poll):
        """ Get an instance of the schema used to render a form for editing settings.
            This form doesn't have any settings, so the schema is empty.
        """
        return colander.Schema()
    
    def get_vote_schema(self, poll):
        """ Get an instance of the schema that this poll uses.
        """
        proposals = poll.get_proposal_objects()
        
        #Choices should be something iterable with the contents [(UID for proposal, Title of proposal), <etc...>, ]
        choices = set()
        
        for prop in proposals:
            choices.add((prop.uid, prop.title))

        class Schema(colander.Schema):
            proposal = colander.SchemaNode(
                            colander.String(),
                            validator=colander.OneOf([x[0] for x in choices]),
                            widget=deform.widget.RadioChoiceWidget(values=choices),
                            title=_(u'Vote for one'),
                            description=_(u''),)

        return Schema()

    def get_vote_class(self):
        return Vote

    def get_result(self, ballots, **settings):
        """ Get the calculated result of this ballot.
            We'll update the ballots with percentage and simply return them.
            The result should look something like this:
            [{'count': 1, 'percentage': 33.33333, ballot': {'proposal': u'af4aa2bc-1ebb-43e1-811b-88ec6ed0e2d1'}}, <etc...>, ]
            Note that percentage is a decimal, not a string.
        """
        if ballots:
            total_votes = sum([x['count'] for x in ballots])
            for result in ballots:
                num = float(result['count']/total_votes)
                result['percentage'] = self._get_percentage(num)
            
            return ballots

    def _get_percentage(self, num):
        return u"%s%%" % (round(num*100, 1))
        
    def render_result(self, poll):
        response = {}
        response['result'] = poll.get_poll_result()
        response['get_proposal_by_uid'] = poll.get_proposal_by_uid
        return render('templates/majority_poll.pt', response)
    
def includeme(config):
    register_poll_plugin(MajorityPollPlugin, registry=config.registry)
    