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

$(document).ready(function () {
  $("[data-load-target]").each(function() {
    voteit.load_target(this);
  });
});
