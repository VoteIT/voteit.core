

function update_table_from_response(response) {

  function role_cls(a, role) {
    var role = role.replace('.', '')
    //debugger;
    if (a.item[role] == true) {
      return 'ok text-success';
    }
    return 'minus text-warning';
  }

  var directive = {'tr':
    {'obj<-results':
      {'.first_name': 'obj.first_name',
        '.last_name': 'obj.last_name',
        '.userid': 'obj.userid',
        '.userid@href+': 'obj.userid',
      }
    }
  };

  var roles = ['.role_view', '.role_discuss', '.role_propose', '.role_vote', '.role_moderate', '.role_admin'];
  $.each(roles, function(i, val) {
    directive['tr']['obj<-results'][val + ' .glyphicon@class+'] = function(a) { return role_cls(a, val) }
  })
  
  //Results for email won't be in the list unless you're a moderator
  if (response['moderator'] == true) {
    directive['tr']['obj<-results']['.email'] = 'obj.email';
    directive['tr']['obj<-results']['.email@href+'] = 'obj.email';
  }

  $('table#participants tbody').render(response, directive);
  $('[data-loading-placeholder]').remove();
  $('table#participants tbody').show();
  
  //FIXME: Counters for each type and sorting
}
$(document).ready(function() {
  $('table#participants tbody').hide();
  var request = arche.do_request('./participants.json');
  request.done(update_table_from_response);
});
