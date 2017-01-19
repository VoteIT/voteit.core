// Note: Refactor to generic function
function toggle_support_button(event) {
  event.preventDefault();
  var elem = $(event.currentTarget);
  request = arche.do_request(elem.attr('href'));
  request.done(function(response) {
    if (response['user_in'] == true) {
      elem.addClass('active');
    } else {
      elem.removeClass('active');
    }
    elem.attr('href', response['toggle_url']);
    elem.parents('[data-support]').find('[data-support-count]').html(response['total']);
  });
  request.fail(arche.flash_error);
}
$(document).ready(function() {
  $('body').on('click', '[data-support-btn]', toggle_support_button);
});
