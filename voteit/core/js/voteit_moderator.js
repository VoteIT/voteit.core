if(typeof(voteit) == "undefined"){
  voteit = {};
}
/* attached to the template cogwheel.pt */
voteit.load_cog_menu = function(event) {
  event.preventDefault();
  var elem = $(event.currentTarget);
  arche.actionmarker_feedback(elem, true);
  var url = elem.attr('href');
  var request = arche.do_request(url);
  var target = elem.siblings('.dropdown-menu');
  request.done(function(response) {
    target.html(response);
  });
  request.fail(arche.flash_error);
  request.always(function() {
    arche.actionmarker_feedback(elem, false);
  })
}


/* fixme: refactor to use save button instead of this */
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
//    console.log(url)
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


$(document).ready(function() {
    $('body').on('click', '[data-cogwheel-menu]', voteit.load_cog_menu);
    $('body').on('click', '[data-set-poll]', voteit.set_poll_proposal);
    $('body').on('click', '[data-close-pick-poll]', voteit.close_pick_poll);
    $('body').on('click', '[data-pick-poll]', voteit.pick_poll);
});
