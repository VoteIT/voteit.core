
/* PROPOSALS */
var ProposalsHandler = function (url) {
  this.url = url;
  //Template will be hidden
  this.tpl = $('[data-template="proposal"]').clone();
  $('[data-template="proposal"]').remove();
  this.base_directive = {'[data-template="proposal"]': {'obj<-contents': {}}};
}
ProposalsHandler.prototype.fetch_data = function() {
  var request = arche.do_request(this.url);
  var that = this;
  request.done(function(response) { that.handle_response(response); });
}
ProposalsHandler.prototype.handle_response = function(response) {
  var directive = this.base_directive;
  directive['[data-template="proposal"]']['obj<-contents'] = response['directives'];
  directive['[data-template="proposal"]']['obj<-contents']['[data-unread]@class+'] = function(a) {
    if (a.item['unread'] == true) return ' list-group-item-unread';
  }
  directive['[data-template="proposal"]']['obj<-contents']['[data-unread]@data-unread'] = "obj.unread";

  $('[data-proposals]').html(this.tpl.clone());
  $('[data-proposals]').render(response, directive);
  voteit.ai_filter.apply_filter(response['show_docids']);
}

/* DISCUSSION */
var DiscussionHandler = function (url) {
  this.url = url;
  this.tpl = $('[data-template="discussion_post"]').clone();
  $('[data-template="discussion_post"]').remove();
  this.base_directive = {'[data-template="discussion_post"]': {'obj<-contents': {}}};
}
DiscussionHandler.prototype.fetch_data = function() {
  var request = arche.do_request(this.url);
  var that = this;
  request.done(function(response) { that.handle_response(response); });
}
DiscussionHandler.prototype.handle_response = function(response, insert_before) {
  $('[data-discussion-posts] [data-initial-loadstate]').remove();
  var directive = this.base_directive;
  directive['[data-template="discussion_post"]']['obj<-contents'] = response['directives'];
  directive['[data-template="discussion_post"]']['obj<-contents']['[data-unread]@class+'] = function(a) {
    if (a.item['unread'] == true) return ' list-group-item-unread';
  }
  directive['[data-template="discussion_post"]']['obj<-contents']['[data-unread]@data-unread'] = "obj.unread";
  $.each(response['batch'], function(i, val) {
    if ($('[data-docid="' + val + '"]').length > 0) {
      console.log('FIXME: remove object from response: ', val)
    }
  })
  var out = $('<div class="dummy"/>')
  out.html(this.tpl.clone())  
  out = out.render(response, directive);
  if (insert_before == true) {
    $('[data-discussion-posts]').prepend(out.children());    
  } else {    
    $('[data-discussion-posts]').append(out.children());
  }
  if (typeof response['load_next_url'] != 'undefined') {
    $('[data-ai-method="load_next_url"]').attr('href', response['load_next_url']);
    $('[data-ai-method="load_next_url"]').show();
    $('[data-json="load_next_msg"]').html(response['load_next_msg']);
  } else {
    $('[data-ai-method="load_next_url"]').hide();
  }
  if (typeof response['load_previous_url'] != 'undefined') {
    $('[data-ai-method="load_previous_url"]').attr('href', response['load_previous_url']);
    $('[data-ai-method="load_previous_url"]').show();
    $('[data-json="load_previous_msg"]').html(response['load_previous_msg']);
  } else {
    $('[data-ai-method="load_previous_url"]').hide();
  }
  voteit.ai_filter.apply_filter(response['show_docids']);
}


/* FILTERING */
var FilterHandler = function() {
  this.filter_tags = [];
  this.show_hidden = false;
}

FilterHandler.prototype.apply_filter = function(show_docids) {
  $('[data-type-name]').hide();
  $.each(show_docids, function(i, val) {
    $('[data-docid="' + val + '"]').show();
  });
}
FilterHandler.prototype.handle_filter_response = function(response) {
  //More stuff here later...
  this.apply_filter(response['show_docids']);
  //Good enough test
  if (JSON.stringify(response['tags']) == JSON.stringify(this.filter_tags)) return false;
  this.filter_tags = response['tags'];
  if (response['tags'].length > 0) {
    $('[data-filter-active]').show();
    $('#tag-filter-notification').remove();
    arche.create_flash_message(response['filter_msg'],
        {id: 'tag-filter-notification', slot: 'fixed-msg-bar', auto_destruct: false, type: 'warning'});      
  } else {
    this.reset();
  }
}

FilterHandler.prototype.reset = function() {
  this.filter_tags = [];
  $('[data-filter-active]').hide();
  $('#tag-filter-notification').remove();  
}

FilterHandler.prototype.handle_filter_update = function(event) {
  event.preventDefault();
  var url = $(event.currentTarget).attr('href');
  if ($(event.currentTarget).data('show-hidden') == true) {
    this.show_hidden = true;
    $('[data-show-hidden="true"]').hide();
    $('[data-show-hidden="false"]').show();
  }
  if ($(event.currentTarget).data('show-hidden') == false) {
    this.show_hidden = false;
    $('[data-show-hidden="true"]').show();
    $('[data-show-hidden="false"]').hide();
  }
  if ($(event.currentTarget).data('tag-reset') == true) {
    this.reset();
  }
  var request = arche.do_request(url, {data: {show_hidden: this.show_hidden, tag: this.filter_tags}});
  var that = this;
  request.done(function(response) { that.handle_filter_response(response); });
}


$(document).ready(function() {
  voteit.ai_filter = new FilterHandler();

  $('body').on('click', '[data-ai-method="load_previous_url"]', function(event) {
    event.preventDefault();
    voteit.ai_filter.reset();
    $('[data-ai-method="load_previous_url"]').hide()
    var url = $(event.currentTarget).attr('href');
    var request = arche.do_request(url);
    request.done(function(response) { voteit.discussion.handle_response(response, true); });
  });
  $('body').on('click', '[data-ai-method="load_next_url"]', function(event) {
    event.preventDefault();
    voteit.ai_filter.reset();
    $('[data-ai-method="load_next_url"]').hide()
    var url = $(event.currentTarget).attr('href');
    var request = arche.do_request(url);
    request.done(function(response) { voteit.discussion.handle_response(response); });
  });

  $('body').on('click', '[data-tag-filter]', function(event) {
    voteit.ai_filter.handle_filter_update(event);
  });

});