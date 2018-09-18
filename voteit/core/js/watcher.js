/* Notify users of events and important things going on.
 * 
 * If you need to extend this, add callbacks to it and modify
 * the response in the view voteit.core.views.watcher. (See Pyramid docs for that)
 *  
 *  */

// FIXME: Fix structure. Use setTimeout instead and try to simplify
// Prepare for sockets change

var Watcher = function(action_url, params) {
  params = typeof params !== 'undefined' ? params : {};
  this.interval = typeof params['interval'] !== 'undefined' ? params['interval'] : 6000;
  this.timer = null;
  this.timer_active = false;
  this.cachekey = ''; //FIXME: Allow multiple later on
  this.max_fails = typeof params['max_fails'] !== 'undefined' ? params['max_fails'] : 10;
  this.current_fails = 0;
  this.action_url = action_url;
  this.debug = typeof params['debug'] !== 'undefined' ? params['debug'] : false;
  this.dmsg("Initialized watcher with url: " + action_url + " and params: " + params);
  this.callbacks = [];
  //FIXME: Other params?
};

Watcher.prototype.dmsg = function(msg) {
  // FIXME: Remove msg var and catch all arguments from 'arguments' instead. (Like the logger)
  if (this.debug == true) {
    console.log(msg);
  }
};

Watcher.prototype.start = function() {
  if (this.timer_active === false) {    
    this.dmsg("Start");
    this.timer_active = true
    var that = this;
    var interval = this.interval;
    if (this.current_fails != 0) {
      interval = this.interval * this.current_fails;
      this.dmsg('Slowing down timer due to fails, interval now: ' + interval)
    }
    this.timer = setInterval(function() { that.fetch_data() }, interval);  
  } else {
    this.dmsg("Timer already running");
  }
};

Watcher.prototype.stop = function() {
  this.dmsg("Stop");
  this.timer = clearInterval(this.timer);
  this.timer_active = false
};

Watcher.prototype.fetch_data = function() {
  if (document.hidden == true) {
    this.dmsg('Document is hidden, waiting with update');
    return
  }
  if (typeof(this.action_url) != 'string') {
    this.dmsg('No action url set, waiting with update');
    return
  }

  this.dmsg('Fetching data from: ' + this.action_url);
  this.stop();
  if (typeof(this.action_url) != 'string') throw "Can't fetch data without an action_url set. Use setup(<url>)";
  var request = arche.do_request(this.action_url, {data: {cachekey: this.cachekey}});
  var that = this;
  request.done(function(response) {
    that.dmsg('Response success');
    that.dmsg(response);
    that.current_fails = 0;
    that.apply_callbacks(response);
    that.start()
  });
  request.fail(function(jqxhr) {
    that.current_fails++;
    that.dmsg('Response fail, fails are now at: ' + that.current_fails);
    if (that.current_fails >= that.max_fails) {
      that.dmsg('Stopping due to too many fails');
    } else {
      that.dmsg('Failed and retrying.');
      that.start();
    }
  })
}

Watcher.prototype.add_response_callback = function(callback) {
  this.dmsg('Adding callback: ' + callback.name);
  this.callbacks.push(callback);
}

Watcher.prototype.apply_callbacks = function(response) {
  var that = this;
  this.callbacks.forEach(function(callback) {
    that.dmsg('Executing callback: ' + callback.name);
    callback(response);
  })
}

voteit.watcher = new Watcher();


window.addEventListener('offline', function(event) {
    voteit.watcher.dmsg('Browser offline, stopping watcher');
    voteit.watcher.stop();
});

window.addEventListener('online', function(event) {
    voteit.watcher.dmsg('Browser online, starting watcher');
    try { voteit.watcher.start(); } catch(e) { voteit.watcher.dmsg("Watcher couldn't start"); }
});
