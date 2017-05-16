
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


voteit.reload_target = function (event) {
  event.preventDefault();
  var elem = $(event.currentTarget);
  arche.actionmarker_feedback(elem, true);
  var request = voteit.load_target(elem.data('reload-target'));
  request.always(function() {
    arche.actionmarker_feedback(elem, false);
    arche.load_flash_messages();
  });
}


/* Adds an attribute to regular popover events and initializes them.
 * Fetches content for the popover from an external source (href) */
voteit.external_popover_from_event = function (event) {
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


$(document).ready(function () {
  $("[data-load-target]").each(function() {
    voteit.load_target(this);
  });
  $('body').on('click', '[data-reload-target]', voteit.reload_target);
  $('body').on('click', '[data-clickable-target]', voteit.load_and_replace);
  $('body').on('click', '[data-external-popover-loaded="false"]', voteit.external_popover_from_event);
});
