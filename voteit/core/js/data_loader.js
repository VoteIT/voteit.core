$(document).ready(function () {
  $("[data-load-target]").each(function() {
    target = $(this);
    var url = target.data('load-target');
    var request = arche.do_request(url);
    request.done(function(data, textStatus, jqXHR) {
      target.html(data);
    });
  });
});
