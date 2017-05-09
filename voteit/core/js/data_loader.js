
voteit.load_target = function (target) {
    var target = $(target);
    var url = target.data('load-target');
    var request = arche.do_request(url);
    request.target = target;
    request.done(function(response) {
        request.target.html(response);
        //maybe scroll?
        var uid = window.location.hash.slice(1);
        var elem = $('[data-uid="' + uid + '"]');
        if (elem.length == 1) {
            elem.goTo();
        }
    });
    request.fail(arche.flash_error);
    return request
}

function reload_target(event) {
  event.preventDefault();
  var elem = $(event.currentTarget);
  arche.actionmarker_feedback(elem, true);
  var request = voteit.load_target(elem.data('reload-target'));
  request.always(function() {
    arche.actionmarker_feedback(elem, false);
    arche.load_flash_messages();
  });
}
voteit.reload_target = reload_target;


/* Adds an attribute to regular popover events and initializes them.
 * Fetches content for the popover from an external source (href) */
function external_popover_from_event(event) {
  event.preventDefault();
  var elem = $(event.currentTarget);
  if (elem.data('external-popover-loaded') == false) {
    var url = elem.attr('href');
    var request = arche.do_request(url);
    request.done(function(response) {
      elem.data('external-popover-loaded', null);
      elem.popover({content: response, html: true});
      elem.popover('show');
    });
    request.fail(arche.flash_error);
  }
}
voteit.external_popover_from_event = external_popover_from_event;

voteit.load_and_replace = function (event) {
  event.preventDefault();
  var elem = $(event.currentTarget);
  arche.actionmarker_feedback(elem, true);
  var url = elem.attr('href');
  var request = arche.do_request(url);
  var target = $(elem.data('replace-target'))
  if (target.length != 1) {
    target = elem;
  }
  request.done(function(response) {
    target.replaceWith(response);
  });
  request.fail(arche.flash_error);
  request.always(function() {
    arche.actionmarker_feedback(elem, false);
    arche.load_flash_messages();
  });
  return request;
}


voteit.load_polls_menu = function (event) {
  // Remember that the menu could be closed via a click too.
  var elem = $(event.currentTarget);
  if (elem.data('menu-loaded') == true) return;
  voteit.reset_polls_menu();
  var menu_target = $('[data-polls-menu-target]');
  arche.actionmarker_feedback(menu_target, true);
  var url = elem.data('polls-menu');
  var request = arche.do_request(url);
  request.done(function(response) {
    menu_target.html(response);
    elem.data('menu-loaded', true)
  });
  request.fail(function(jqxhr) {
    arche.flash_error(jqxhr);
    arche.actionmarker_feedback(menu_target, false);
  });
}


voteit.reset_polls_menu = function() {
  var out = '<li role="presentation" class="disabled">';
  out += '<a role="menuitem" tabindex="-1" href="#">';
  out += '<span data-actionmarker="glyphicon glyphicon-refresh rotate-me"></span>';
  out += $('[data-polls-menu-target]').data('placeholder');
  out += '</a></li>';
  $('[data-menu-loaded]').data('menu-loaded', false);
  $('[data-polls-menu-target]').html(out);
}


voteit.insert_ai_response = function(response, elem) {
    var target = $(elem.data('load-agenda-item'));
    $('[data-load-agenda-item]').removeClass('active');
    elem.addClass('active');
    target.html(response);
    target.find("[data-load-target]").each(function() {
        voteit.load_target(this);
    });
}


voteit.make_ai_request = function(elem) {
    var url = elem.attr('href');
    //arche.actionmarker_feedback(elem, true);
    var target = $(elem.data('load-agenda-item'));
    var request = arche.do_request(url);
    request.done(function(response) {
        voteit.insert_ai_response(response, elem);
    });
    request.fail(arche.flash_error);
    request.always(function() {
        //arche.actionmarker_feedback(elem, false);
        arche.load_flash_messages();
    });
    return request;
}


voteit.load_agenda_item = function(event) {
    event.preventDefault();
    var elem = $(event.currentTarget);
    var url = elem.attr('href');
    var request = voteit.make_ai_request(elem);
    request.done(function(response) {
        var title = elem.find('[data-title]').text();
        document.title = title;
        window.history.pushState(
            {'url': url, 'title': title, 'html': response, 'type': 'agenda_item'},
        title, url);
        voteit.hide_nav('#fixed-nav');
    });
}


voteit.load_profile_menu = function() {
    //var request = arche.do_request('/_user_menu');
    if ($('#user-menu').hasClass('activated')) {
        $('#user-menu').empty();
        voteit.hide_nav("#user-menu");

    } else {
        var request = arche.do_request('/_user_menu');
        request.done(function(response) {
            voteit.show_nav("#user-menu");

            $('#user-menu').html(response);
        });
    }

}
/*
voteit.initial_ai_loaded function() {

    var curr_url = document.location.href;
    var curr_title = document.title;
    var curr_type = $('[data-load-agenda-item][href="' + curr_url + '"]').length > 0 ? 'agenda_item' : '';

    var elem = $();
    var url = elem.attr('href');
    var request = voteit.make_ai_request(elem);
    request.done(function(response) {
        var title = elem.find('[data-title]').text();
        document.title = title;
        window.history.pushState(
            {'url': url, 'title': title, 'html': response, 'type': 'agenda_item'},
        title, url);
    });
}*/

/*
voteit.handle_agenda_back = function(event) {

//    console.log('popstate fired!');
//    console.log(event.state);
    try {
        if (event.state['type'] != 'agenda_item') return;
    } catch(e) {
        return;
    }

    var elem = $('[href="' + event.state['url'] + '"]');
    var target = $(elem.data('load-agenda-item'));
    voteit.insert_ai_response(event.state['html'], elem);
}
*/

//window.addEventListener('popstate', voteit.handle_agenda_back);


$(document).ready(function () {
  $("[data-load-target]").each(function() {
    voteit.load_target(this);
  });
  $('body').on('click', '[data-reload-target]', voteit.reload_target);
  $('#polls-menu').on('hidden.bs.dropdown', voteit.reset_polls_menu);
  $('body').on('click', '[data-clickable-target]', voteit.load_and_replace);
  $('body').on('click', '[data-polls-menu]', voteit.load_polls_menu);
  $('body').on('click', '[data-external-popover-loaded="false"]', voteit.external_popover_from_event);
  $('body').on('click', '[data-load-agenda-item]', voteit.load_agenda_item);
});
