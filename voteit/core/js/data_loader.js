
function load_target(target) {
  var target = $(target);
  var url = target.data('load-target');
  var request = arche.do_request(url);
  request.target = target;
  request.done(function(data, status, xhr) {
    request.target.html(data);
  });
  request.fail(arche.flash_error);
  return request
}
voteit.load_target = load_target;

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

function load_and_replace(event) {
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
}
voteit.load_and_replace = load_and_replace;


function load_polls_menu(event) {
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
voteit.load_polls_menu = load_polls_menu;

function reset_polls_menu() {
  var out = '<li role="presentation" class="disabled">';
  out += '<a role="menuitem" tabindex="-1" href="#">';
  out += '<span data-actionmarker="glyphicon glyphicon-refresh rotate-me"></span>';
  out += $('[data-polls-menu-target]').data('placeholder');
  out += '</a></li>';
  $('[data-menu-loaded]').data('menu-loaded', false);
  $('[data-polls-menu-target]').html(out);
}
voteit.reset_polls_menu = reset_polls_menu;


voteit.set_poll_proposal = function(event) {
    var elem = $(event.currentTarget);
    var form = elem.parents('form');
    arche.actionmarker_feedback(elem, true);
    var request = arche.do_request(elem.data('url'), {data: form.serialize(), method: 'POST'});
    request.done(function(response) {
        var poll_elem = $('[data-uid="' + elem.data('set-poll') + '"]');
        poll_elem.replaceWith(response);
    });
    request.always(function() {
        arche.actionmarker_feedback(elem, false);
    });
}


voteit.pick_poll = function(event) {
    event.preventDefault();
    var elem = $(event.currentTarget);
    var url = elem.attr('href');
    var will_remove = $(elem.data('will-remove'));
    console.log(url)
    if (will_remove.length > 0) {
        //Remove
        will_remove.remove();
    } else {
        arche.actionmarker_feedback(elem, true);
        //Load
        var request = arche.do_request(url);
        request.done(function(response) {
            $.each(response, function(i, val) {
                $('[data-uid="' + i + '"]').after(val);
            });
        });
        request.always(function() {
            arche.actionmarker_feedback(elem, false);
        });
    }
}


voteit.close_pick_poll = function(event) {
    $("[data-pick-poll-context]").remove();
}


$(document).ready(function () {
  $("[data-load-target]").each(function() {
    voteit.load_target(this);
  });
  $('body').on('click', '[data-reload-target]', voteit.reload_target);
  $('#polls-menu').on('hidden.bs.dropdown', voteit.reset_polls_menu);
  $('body').on('click', '[data-clickable-target]', voteit.load_and_replace);
  $('body').on('click', '[data-polls-menu]', voteit.load_polls_menu);
  $('body').on('click', '[data-external-popover-loaded="false"]', voteit.external_popover_from_event);
  $('body').on('click', '[data-set-poll]', voteit.set_poll_proposal);
  $('body').on('click', '[data-close-pick-poll]', voteit.close_pick_poll);
  $('body').on('click', '[data-pick-poll]', voteit.pick_poll);

});
