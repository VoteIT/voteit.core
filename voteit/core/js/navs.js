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


voteit.show_agenda = function() {
    //Figure out which agenda to use
    var elem =  $('[data-agenda-url]');
    if (elem.length > 0) {
        var url = elem.data('agenda-url');
        var request = arche.do_request(url);
        arche.actionmarker_feedback(elem, true);
        request.done(function(response) {
            elem.replaceWith(response);
        });
    }
    if (request) {
        request.always(function() {
            arche.actionmarker_feedback(elem, false);
        });
    }

//  request.fail(arche.flash_error);

    //FIXME: Can we tie this to bootstraps grid float breakpoint var?
    if ($(window).width() > 768) {
        //Desktop version
        $('body').addClass('left-fixed-active');
        //voteit.toggle_nav('#fixed-nav');
        $('#fixed-nav').addClass('activated');
        document.cookie = "voteit.hide_agenda=;path=/";
    } else {
        //Small version
        voteit.show_nav('#fixed-nav');
    }
}


voteit.hide_agenda = function() {
    if ($(window).width() > 768) {
        $('body').removeClass('left-fixed-active');
        $('#fixed-nav').removeClass('activated');
        document.cookie = "voteit.hide_agenda=1;path=/";
    } else {
        //Small version
        voteit.hide_nav('#fixed-nav');
    }
}


voteit.toggle_agenda = function() {
    if ($('#fixed-nav').hasClass('activated')) {
        voteit.hide_agenda();
    } else {
        voteit.show_agenda();
    }
}


voteit.init_agenda = function(show_in_fullscreen) {
    //Decide what to do depending on resolution etc
    if ($(window).width() > 768) {
        if (show_in_fullscreen == true) voteit.show_agenda();
    } else {
        // Small screen
        $('#fixed-nav').data('slide-menu', 'fixed-nav').addClass('slide-in-nav');
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
        if ($(window).width() < 768) voteit.hide_nav('#fixed-nav');
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
    console.log(response['unvoted_polls']);
    if (response['unvoted_polls'] == 0) {
        $('[data-important-polls]').empty();
    } else {
        $('[data-important-polls]').html(response['unvoted_polls']);
    }
};


$(document).ready(function () {
    voteit.watcher.add_response_callback(unvoted_counter);
    $('body').on('click', '[data-load-agenda-item]', voteit.load_agenda_item);
});
