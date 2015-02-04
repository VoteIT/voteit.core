
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

$(document).ready(function () {
  $("[data-load-target]").each(function() {
    load_target(this);
  });
});
