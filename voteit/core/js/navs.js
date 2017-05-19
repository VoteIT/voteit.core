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

    //FIXME: Can we tie this to bootstraps grid float breakpoint var?
    if ($(window).width() > 768) {
        //Desktop version
        $('body').addClass('left-fixed-active');
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
    target.html(response);
    target.find("[data-load-target]").each(function() {
        voteit.load_target(this);
    });
}


voteit.make_ai_request = function(elem) {
    var url = elem.attr('href');
    arche.actionmarker_feedback(elem, true);
    var target = $(elem.data('load-agenda-item'));
    var request = arche.do_request(url);
    request.done(function(response) {
        voteit.set_active_ai(elem.data('ai-name'));
        //Fixme: Make sure it's an item in the agenda :)
        voteit.insert_ai_response(response, elem);
    });
    request.fail(arche.flash_error);
    request.always(function() {
        arche.actionmarker_feedback(elem, false);
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


voteit.load_agenda_data = function(state) {
    var tpl = $('[data-purejs-template="agenda-item"]').clone();
    tpl.removeAttr('data-purejs-template');

    var directive = {'a':
        {'ai<-ais':
            {
                '.@href+': 'ai.name',
                '[data-ai="title"]': 'ai.title',
                '[data-ai="prop_count"]': 'ai.contents.Proposal.total',
                '[data-ai="disc_count"]': 'ai.contents.DiscussionPost.total',
                '[data-ai="poll_count"]': 'ai.contents.Poll.total',
                '.@data-ai-name': 'ai.name',
                '.@class+': function(arg) {
                    if (arg.item.contents.Proposal.unread > 0 || arg.item.contents.DiscussionPost.unread > 0) {
                        return ' item-unread';
                    }
                },
                '[data-ai="prop_unread"]': function(arg) {
                    if (arg.item.contents.Proposal.unread > 0) {
                        return arg.item.contents.Proposal.unread;
                    }
                },
                '[data-ai="disc_unread"]': function(arg) {
                    if (arg.item.contents.DiscussionPost.unread > 0) {
                        return arg.item.contents.DiscussionPost.unread;
                    }
                }
            },
            // same kind of sort as the usual Array sort
            sort: function(a, b){
              var cmp = function(x, y){
                return x > y? 1 : x < y ? -1 : 0;
              };
              if (typeof voteit.agenda_sort_order == 'undefined') {
                return cmp(a.name, b.name);
              } else {
                return cmp( voteit.agenda_sort_order.indexOf(a.name), voteit.agenda_sort_order.indexOf(b.name) );
              }
            }
        }
    };

    var control_elem = $('[data-agenda-control="' + state + '"]');
    arche.actionmarker_feedback(control_elem, true);

    var request = arche.do_request(voteit.agenda_data_url, {method: 'POST', data: {state: state}});
    request.done(function(response) {
        var target = $('[data-agenda-state="' + state + '"]');
        target.html(tpl.html());
        target.render(response, directive);
        control_elem.removeClass('collapsed');
        //Agendas might have set it without effect
        if (voteit.active_ai_name) voteit.set_active_ai(voteit.active_ai_name);
    });
    request.always(function() {
        arche.actionmarker_feedback(control_elem, false);
    });
    return request;
}


voteit.handle_ai_state_toggles = function(event) {
    var elem = $(event.currentTarget);
    var state = elem.data('agenda-control');
    if (elem.hasClass('collapsed')) {
        //Load item
        var request = voteit.load_agenda_data(state);
    } else {
        //Collapse and remove
        voteit.agenda_collapse_ai_state(state);
    }
}


voteit.agenda_collapse_ai_state = function(state) {
    if (state) {
        var elem = $('[data-agenda-control="' + state + '"]');
        var target = $('[data-agenda-state="' + state + '"]');
    } else {
        var elem = $('[data-agenda-control]');
        var target = $('[data-agenda-state]');
    }
    elem.addClass('collapsed');
    target.empty();
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
    if (response['unvoted_polls'] == 0) {
        $('[data-important-polls]').empty();
    } else {
        $('[data-important-polls]').html(response['unvoted_polls']);
    }
};


function agenda_states(response) {
  $.each(response.agenda_states, function(k, v) {
    $('[data-ai-state-count="' + k + '"]').text(v);
  });
}


voteit.active_ai_name = '';


voteit.set_active_ai = function(name) {
    $('[data-ai-name]').removeClass('active');
    var elem = $('[data-ai-name="' + name + '"]');
    if (elem.length>0) {
        elem.addClass('active');
    }
    voteit.active_ai_name = name;
}


voteit.select_ai_tag = function(tag) {
    var request = arche.do_request(voteit.agenda_select_tag_url, {method: 'POST', data: {tag: tag}});
    request.done(function(response) {
        voteit.watcher.fetch_data();
        $('[data-select-tag]').removeClass('active');
        $('[data-select-tag="' + tag + '"]').addClass('active');
        voteit.agenda_collapse_ai_state();
    });
}


$(document).ready(function () {
    voteit.watcher.add_response_callback(unvoted_counter);
    voteit.watcher.add_response_callback(agenda_states);
    $('body').on('click', '[data-load-agenda-item]', voteit.load_agenda_item);
    $('body').on('click', '[data-agenda-control]', voteit.handle_ai_state_toggles);
});
