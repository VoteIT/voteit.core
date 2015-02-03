
function load_target(target) {
  var target = $(target);
  var url = target.data('load-target');
  var request = arche.do_request(url, {async: true});
  request.target = target;
  request.done(function(data, textStatus, jqXHR) {
    request.target.html(data);
  });
  return request
}

$(document).ready(function () {
  $("[data-load-target]").each(function() {
    load_target(this);
  });
});
