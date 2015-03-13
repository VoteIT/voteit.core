if(typeof(voteit) == "undefined"){
    voteit = {};
}

function load_target(target) {
  var target = $(target);
  var url = target.data('load-target');
  var request = arche.do_request(url);
  request.target = target;
  request.done(function(data, status, xhr) {
    request.target.html(data);
  });
  return request
}
voteit.load_target = load_target;

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
  var url = elem.attr('href');
  var request = arche.do_request(url);
  request.done(function(response) {
    elem.parent().html(response);
  });
  request.fail(arche.flash_error);
}
voteit.load_and_replace = load_and_replace;

function reply_to(event) {
  event.preventDefault();
  //FIXME: Warn??
  $('[data-reply]').remove();
  var elem = $(event.currentTarget);
  var url = elem.attr('href');
  var request = arche.do_request(url);
  request.done(function(response) {
    var target = elem.parent('.list-group-item');
    target.after('<div class="panel-footer" data-reply>' + response + '</div>');
    $('[data-reply]').hide().slideDown();
  });
  request.fail(arche.flash_error);

  //$('html, body').animate({
  //  scrollTop: btn.offset().top
  //}, 1000);
}
voteit.reply_to = reply_to;

$(document).ready(function () {
  $("[data-load-target]").each(function() {
    voteit.load_target(this);
  });

  $('body').on('click', '[data-clickable-target]', voteit.load_and_replace);
  $('body').on('click', '[data-reply-to]', voteit.reply_to);
  
  $('body').on('click', '[data-external-popover-loaded="false"]', voteit.external_popover_from_event);
});
