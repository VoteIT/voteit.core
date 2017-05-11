if(typeof(voteit) == "undefined"){
    voteit = {};
}


voteit.toggle_nav = function(selector) {
    if ($(selector).hasClass('activated')) {
        voteit.hide_nav(selector);
    } else {
        voteit.show_nav(selector);
    }
}


voteit.show_nav = function(selector) {
    $('[data-slide-menu].activated').removeClass('activated');
    $(selector).addClass('activated');
    $('#fixed-nav-backdrop').data('active-menu', selector);
    $('#fixed-nav-backdrop').fadeIn();
    $('body').css({'overflow': 'hidden'});
}


voteit.hide_nav = function(selector) {
    var selector = (typeof selector == 'string') ? selector : $('#fixed-nav-backdrop').data('active-menu');
    $(selector).removeClass('activated');
    $('#fixed-nav-backdrop').fadeOut();
    $('#fixed-nav-backdrop').data('active-menu', null);
    $('body').css({'overflow': 'visible'});
}


voteit.load_inline_menu = function(selector, url) {
    if ($(selector).hasClass('activated')) {
        $(selector).empty();
        voteit.hide_nav(selector);
    } else {
        var request = arche.do_request(url);
        request.done(function(response) {
            voteit.show_nav(selector);
            $(selector).html(response);
        });
    }
}


voteit.insert_ai_response = function(response, elem) {
    var target = $(elem.data('load-agenda-item'));
    $('[data-load-agenda-item]').removeClass('active');
    elem.addClass('active');
    target.html(response);
    target.find("[data-load-target]").each(function() {
        voteit.load_target(this);
    });
}


voteit.make_ai_request = function(elem) {
    var url = elem.attr('href');
    //arche.actionmarker_feedback(elem, true);
    var target = $(elem.data('load-agenda-item'));
    var request = arche.do_request(url);
    request.done(function(response) {
        voteit.insert_ai_response(response, elem);
    });
    request.fail(arche.flash_error);
    request.always(function() {
        //arche.actionmarker_feedback(elem, false);
        arche.load_flash_messages();
    });
    return request;
}


voteit.load_agenda_item = function(event) {
    event.preventDefault();
    var elem = $(event.currentTarget);
    var url = elem.attr('href');
    var request = voteit.make_ai_request(elem);
    request.done(function(response) {
        var title = elem.find('[data-title]').text();
        document.title = title;
        window.history.pushState(
            {'url': url, 'title': title, 'html': response, 'type': 'agenda_item'},
        title, url);
        voteit.hide_nav('#fixed-nav');
    });
}



/*
voteit.initial_ai_loaded function() {

    var curr_url = document.location.href;
    var curr_title = document.title;
    var curr_type = $('[data-load-agenda-item][href="' + curr_url + '"]').length > 0 ? 'agenda_item' : '';

    var elem = $();
    var url = elem.attr('href');
    var request = voteit.make_ai_request(elem);
    request.done(function(response) {
        var title = elem.find('[data-title]').text();
        document.title = title;
        window.history.pushState(
            {'url': url, 'title': title, 'html': response, 'type': 'agenda_item'},
        title, url);
    });
}*/

/*
voteit.handle_agenda_back = function(event) {

//    console.log('popstate fired!');
//    console.log(event.state);
    try {
        if (event.state['type'] != 'agenda_item') return;
    } catch(e) {
        return;
    }

    var elem = $('[href="' + event.state['url'] + '"]');
    var target = $(elem.data('load-agenda-item'));
    voteit.insert_ai_response(event.state['html'], elem);
}
*/

//window.addEventListener('popstate', voteit.handle_agenda_back);


function unvoted_counter(response) {

    $('[data-important-polls]').html(response['unvoted_polls']);

    if (response['unvoted_polls'] > 0 && $('#poll-notification').length == 0) {
        //arche.create_flash_message("Halli hallå?",
        //{id: 'poll-notification', slot: 'fixed-msg-bar', auto_destruct: false, type: 'success'});
    }
    if (response['unvoted_polls'] == 0 && $('#poll-notification').length != 0) {
        $('#poll-notification').remove();
    }

};


$(document).ready(function () {
    voteit.watcher.add_response_callback(unvoted_counter);
    $('body').on('click', '[data-load-agenda-item]', voteit.load_agenda_item);
});
