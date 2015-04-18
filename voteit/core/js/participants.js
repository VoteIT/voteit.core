
function update_table_from_response(response) {

  function role_cls(a, role) {
    var role = role.replace('.', '')
    if (a.item[role] == 1) {
      return 'glyphicon glyphicon-ok text-success';
    }
    return 'glyphicon glyphicon-minus text-warning';
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
    var role_view_name = val.replace('.', '')
    directive['tr']['obj<-results'][val + ' [data-perm-marker]@class'] = function(a) { return role_cls(a, val) }
    if (response['moderator'] == true && val !== '.role_admin') {
      directive['tr']['obj<-results'][val + ' [data-permission-toggle]@data-enabled'] = function(a) {
        //false is empty, so set it explicitly
        return a.item[role_view_name] == 1 ? 1 : 0;
      }
    }
    $('[data-role-count="' + role_view_name + '"]').html(response['role_count'][role_view_name])
  });

  //Results for email won't be in the list unless you're a moderator
  if (response['moderator'] == true) {
    directive['tr']['obj<-results']['[data-permission-toggle]@data-userid'] = 'obj.userid';
    directive['tr']['obj<-results']['.email'] = 'obj.email';
    directive['tr']['obj<-results']['.email@href+'] = 'obj.email';
  }

  $('table#participants tbody').render(response, directive);
  $('[data-loading-placeholder]').remove();
  $('table#participants tbody').show();
  
  //FIXME: Counters for each type and sorting
}

function handle_permission_toggle(event) {
  event.preventDefault();
  var elem = $(event.currentTarget);
  var data = {}
  data['role'] = elem.data('role');
  data['enabled'] = elem.data('enabled');
  data['userid'] = elem.data('userid');
  var request = arche.do_request(elem.attr('href'), {data: data, method: 'POST'});
  request.done(permission_toggle_response);
  request.fail(arche.flash_error);
}
function permission_toggle_response(response) {
  //FIXME: Total count doesn't change
  var elem = $('[data-permission-toggle][data-role="' + response['role'] + '"][data-userid="' + response['userid'] + '"]');
  var marker = elem.children('[data-perm-marker]');
  //FIXME: Make this smarter some day...
  if (response['status'] === true) {
    elem.data('enabled', 1);
    marker.replaceWith('<span data-perm-marker class="glyphicon glyphicon-ok text-success">')
  } else {
    elem.data('enabled', 0);
    marker.replaceWith('<span data-perm-marker class="glyphicon glyphicon-minus text-warning">')
  }
}

$(document).ready(function() {
  $('table#participants tbody').hide();
  var request = arche.do_request('./participants.json');
  request.done(update_table_from_response);
  $('body').on('click', '[data-permission-toggle]', handle_permission_toggle);
});
