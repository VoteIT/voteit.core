if(typeof(voteit) == "undefined"){
  voteit = {};
}
/* attached to the template cogwheel.pt */
function load_cog_menu(event) {
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
voteit.load_cog_menu = load_cog_menu;

$(document).ready(function() {
  $('body').on('click', '[data-cogwheel-menu]', voteit.load_cog_menu);
});
