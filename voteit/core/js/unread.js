/* Depends on base */

var UnreadHandler = function() {
  this.timer = null;
  this.interval = 6000;
  this.url = null;

  this.start = function() {
    this.stop();
    var that = this;
    this.timer = setInterval(function() { that.notify(); }, this.interval);
  }
  this.stop = function() {
    if (this.timer != null) {
      this.timer = clearInterval(this.timer);
    }
  }
  this.notify = function() {
    this.stop();
    
    if (!this.url) {
      this.start();
      return false;
    }
    
    var unread_uids = [];
    $("[data-unread]:visible").each( function(i, val) {
      if ($(val).data('unread') === true) unread_uids.push( $(val).data('uid') );
    });
    
    if (unread_uids.length > 0) {
      // There's data to send
      var request = arche.do_request(this.url, {method: 'POST', data:{'read_uids': unread_uids}});
      var that = this;
      request.always(function() {
        that.start();
      });
      request.done(function(response) {
        //Remove uids here
        if ('marked_read' in response) {
          $(response['marked_read']).each(function() {
            $('[data-uid=' + this + ']').data('unread', false);
          });
        }
      });
    } else {
      // There were no unreads - restart
      this.start();
    }
  }
}


$(document).ready(function() {
  voteit.unread = new UnreadHandler();
});


$(window).on("blur focus", function(e) {
  var prevType = $(this).data("prevType");
  if (prevType != e.type) {   //Reduce 'double fire' issues
    switch (e.type) {
      case "blur":
        if (typeof voteit.unread != 'undefined') voteit.unread.stop();
        break;
      case "focus":
        if (typeof voteit.unread != 'undefined') voteit.unread.start();
        break;
    }
  }
  $(this).data("prevType", e.type);
})
