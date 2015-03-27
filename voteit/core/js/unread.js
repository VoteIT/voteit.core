/* Depends on base */

voteit.unread_notify_timer = null;
voteit.unread_notify_interval = 6000;
voteit.unread_notify_url = null;

function unread_notify(url) {
  if (typeof(url) !== 'undefined') voteit.unread_notify_url = url;
  if (voteit.unread_notify_timer) {
    voteit.unread_notify_timer = clearInterval(voteit.unread_notify_timer);
  }
  if (voteit.unread_notify_url) {
    // Action URL set
    var unread_uids = [];
    $("[data-unread]").each( function() {
      if ($(this).data('unread') === true) unread_uids.push( $(this).data('uid') );
    });
    if (unread_uids.length > 0) {
      // There's data to send
      arche.do_request(voteit.unread_notify_url, {method: 'POST', data:{'read_uids': unread_uids}})
      .always(function() {
        voteit.unread_notify_timer = setInterval(voteit.unread_notify, voteit.unread_notify_interval);
      })
      .done(function(data) {
        //Remove uids here
        if ('marked_read' in data) {
          $(data['marked_read']).each(function() {
            $('[data-uid=' + this + ']').data('unread', false);
          })
        }
      });
    } else {
      // Retry later - but since there was nothing to do, be a bit more slow...
      voteit.unread_notify_timer = setInterval(voteit.unread_notify, voteit.unread_notify_interval + 5000);
    }
  } else {
    // No action URL set
    voteit.unread_notify_timer = setInterval(voteit.unread_notify, voteit.unread_notify_interval);
  }
}
voteit.unread_notify = unread_notify;

$(window).on("blur focus", function(e) {
  var prevType = $(this).data("prevType");
  if (prevType != e.type) {   //  reduce double fire issues
    switch (e.type) {
      case "blur":
        voteit.unread_notify_timer = clearInterval(voteit.unread_notify_timer);
        break;
      case "focus":
        voteit.unread_notify_timer = clearInterval(voteit.unread_notify_timer); //Just to make sure
        voteit.unread_notify_timer = setInterval(voteit.unread_notify, voteit.unread_notify_interval);
        break;
    }
  }
  $(this).data("prevType", e.type);
})
