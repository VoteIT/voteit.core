function update_agenda_from_response(response) {
  var directive = {'#agenda-item-portlet .portlet':
    {'wf_states<-':
      {'.wf-title': 'wf_states.state',
       'li.list-group-item': {'ai<-wf_states.state_ais':
       {
         '.ai-title': 'ai.title',
         '.ai-link@href+': 'ai.__name__',
         '.proposal_count': 'ai.proposal_count',
         '.discussion_count': 'ai.discussion_count'
       }
      }},
    }
  }
  $('#agenda-item-portlet').render(response, directive);
};
