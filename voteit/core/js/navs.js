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
    $('[data-slide-menu].activated').removeClass('activated').hide();
    $(selector).addClass('activated').fadeIn();
    $('#fixed-nav-backdrop').data('active-menu', selector);
    $('#fixed-nav-backdrop').fadeIn();
    $('body').css({'overflow': 'hidden'});
}


voteit.hide_nav = function(selector) {
    var selector = (typeof selector == 'string') ? selector : $('#fixed-nav-backdrop').data('active-menu');
    $(selector).removeClass('activated').fadeOut();
    $('#fixed-nav-backdrop').fadeOut();
    $('#fixed-nav-backdrop').data('active-menu', null);
    $('body').css({'overflow': ''});
}

/*
selector
    Where to load the menu

url
    From where to load

Tag data-initiator="<selector>" should indicate the tag that initiated the call,
mostly for visual feedback during the load process.
*/
voteit.load_inline_menu = function(selector, url) {
    var initiator = $('[data-initiator="' + selector + '"]');
    if (initiator.hasClass('disabled')) return;
    $('.menu-toggler').removeClass('open');
    if ($(selector).hasClass('activated')) {
        $(selector).empty();
        voteit.hide_nav(selector);
    } else {
        arche.actionmarker_feedback(initiator, true);
        var request = arche.do_request(url);
        request.done(function(response) {
            voteit.show_nav(selector);
            console.log(selector);
            $(selector).html(response);
            arche.actionmarker_feedback(initiator, false);
            initiator.addClass('open');
        });
        return request;
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
    $('body').addClass('left-fixed-active');
    if ($(window).width() > 768) {
        //Desktop version
        $('#fixed-nav').addClass('activated').show();
        document.cookie = "voteit.hide_agenda=;path=/";
    } else {
        //Small version
        voteit.show_nav('#fixed-nav');
    }
}


voteit.hide_agenda = function() {
    $('body').removeClass('left-fixed-active');
    if ($(window).width() > 768) {
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
        if (show_in_fullscreen) voteit.show_agenda();
    } else {
        // Small screen
        $('#fixed-nav').data('slide-menu', 'fixed-nav').addClass('slide-in-nav');
        voteit.hide_agenda();
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
                '.@data-ai-name': 'ai.name'
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

    //Update directive depending on contents of ai
    var types_directive = {
        '[data-ai="prop_count"]': 'ai.contents.Proposal.total',
        '[data-ai="disc_count"]': 'ai.contents.DiscussionPost.total',
        '[data-ai="poll_count"]': 'ai.contents.Poll.total',
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
    }

    var control_elem = $('[data-agenda-control="' + state + '"]');
    arche.actionmarker_feedback(control_elem, true);

    var request = arche.do_request(voteit.agenda_data_url, {method: 'POST', data: {state: state}});
    request.done(function(response) {
        if (!response['hide_type_count']) {
            $.extend(directive['a']['ai<-ais'], types_directive);
        }

        var target = $('[data-agenda-state="' + state + '"]');
        target.html(tpl.html());
        target.render(response, directive);
        control_elem.removeClass('collapsed');
        if (response['hide_type_count']) $('[data-agenda-count-cols]').hide();
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
    voteit.adjust_greedy_element();
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


voteit.select_ai_tag = function(tag, load_ongoing) {
    var request = arche.do_request(voteit.agenda_select_tag_url, {method: 'POST', data: {tag: tag}});
    request.done(function(response) {
        voteit.watcher.fetch_data();
        $('[data-select-tag]').removeClass('active');
        $('[data-select-tag="' + tag + '"]').addClass('active');
        voteit.agenda_collapse_ai_state();
        $('[data-agenda-filter]').hide();
        if (tag) {
            $('[data-agenda-filter="true"]').show();
            $('[data-active-agenda-tag]').text(tag);
        } else {
            $('[data-agenda-filter="false"]').show();
        }
        if (load_ongoing == true) {
            voteit.load_agenda_data('ongoing');
        }
    });
}


/* Adjust greedy elements so they won't take up too much space
Structure should be:
    <some-container data-check greedy>
        <other elem> ...
        <greedy_elem class="greedy">
    </some-container>
*/
voteit.adjust_greedy_element = function(extra_margin) {
    //16 due to rounding elements. Sometimes widths will be like 102.32px
    var extra_margin = (typeof extra_margin == 'undefined') ? 1 : extra_margin;
    $('[data-check-greedy]').each(function(i, elem) {
        var elem = $(elem);
        var total_width = elem.width();
        var locked_width = 0;
        $.each(elem.children('*:visible:not(.greedy)'), function(k, v) {
            locked_width += Math.ceil($(v).outerWidth( true ));
        });
        elem.find('.greedy').css({'width': total_width-locked_width-extra_margin});
    });
}

voteit.greedyMutationListener = function () {
    var innerWidth = document.body.clientWidth;
    var MutationObserver = window.MutationObserver || window.WebKitMutationObserver;
    var observer = new MutationObserver(function(mutations, observer) {
        // fired when a mutation occurs
        var newWidth = document.body.clientWidth;
        if (innerWidth != newWidth) {
            voteit.adjust_greedy_element();
            innerWidth = newWidth;
        }
    });
    observer.observe(document, {
        subtree: true,
        attributes: true,
    });
}


$(document).ready(function () {
    voteit.watcher.add_response_callback(unvoted_counter);
    voteit.watcher.add_response_callback(agenda_states);
    $('body').on('click', '[data-load-agenda-item]', voteit.load_agenda_item);
    $('body').on('click', '[data-agenda-control]', voteit.handle_ai_state_toggles);
    voteit.adjust_greedy_element();
    window.addEventListener('resize', function() {
        voteit.adjust_greedy_element();
    });
    voteit.greedyMutationListener();
});
