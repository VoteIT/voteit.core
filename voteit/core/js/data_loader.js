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
    }) 
  }
}
voteit.external_popover_from_event = external_popover_from_event;


$(document).ready(function () {
  $("[data-load-target]").each(function() {
    voteit.load_target(this);
  });

  $('body').on('click', '[data-external-popover-loaded="false"]', function(event){
    voteit.external_popover_from_event(event);
  })
  
});
