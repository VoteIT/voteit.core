$.ajaxSetup ({
	cache: false
});

$.fn.hasAttr = function(name) {
    var attr = $(this).attr(name);
    return (typeof attr !== 'undefined' && attr !== false);
};

//Disable qtips silly animations
$.fn.qtip.defaults.show['effect'] = false;
$.fn.qtip.defaults.hide['effect'] = false;
$.fn.qtip.defaults.position['effect'] = false;

/* JS that should be present on every page, regardless of its function.*/
if(typeof(voteit) == "undefined"){
    var voteit = {};
}

function spinner() {
    var _spinner = $(document.createElement('img'));
    _spinner.addClass('spinner');
    _spinner.attr('src', '/static/images/spinner.gif');
    _spinner.attr('alt', voteit.translation['waiting']);
    return _spinner;
}

function flash_message(message, attr_class, close_button) {
    var div = $(document.createElement('div'));
    div.addClass('message');
    if(attr_class)
        div.addClass(attr_class);
    var span = $(document.createElement('span'));
    span.html(message);
    div.append(span);
    if(close_button) {
        var button = $(document.createElement('a'));
        button.addClass('close_message');
        button.attr('href', '#');
        button.attr('title', voteit.translation['close_message']);
        button.html('X');
        div.append(button);
    }
    $('#flash_messages').append(div);
}

/* Flash messages */
$(document).ready(function () {
    $('#flash_messages .close_message').live('click', function(event) {
        try { event.preventDefault(); } catch(e) {}
        //Parent of the .close_message class should be .message
        $(this).parent().slideUp(200);
    });
});

$(document).ready(function() {
    // This won't work in IE'
    var div = $('#flash_messages');
    if(div) {
        var start = div.offset().top;
        $.event.add(window, "scroll", function() {
            var p = $(window).scrollTop();
            div.css('position',((p)>start) ? 'fixed' : 'static');
            div.css('top',((p)>start) ? '0px' : '');
        });
   }
});



/* Bind meeting sections menus + possibly other */
$('#global-actions-menu .menu_header').live('hover', function(event) { dropdown_menus(event, this, 'meeting_actions_menu') });
$('#meeting-actions .menu_header').live('hover', function(event) { dropdown_menus(event, this, 'meeting_actions_menu') });
function dropdown_menus(event, hover_object, css_classes) {
    /* stop form using default action
    IE might throw an error calling preventDefault(), so use a try/catch block. */
    try { event.preventDefault(); } catch(e) {}
    var hover_object = $(hover_object);
    if (hover_object.hasAttr('url')) {
        var url = hover_object.attr('url');
        var q_content = { 
            text: voteit.translation['loading'], // The text to use whilst the AJAX request is loading
            ajax: {
                url: url,
            }
        };
    }
    else {
        //We need a copy of the content, otherwise qtip will try to locate it every time it triggers
        var q_content = { text: hover_object.parent().find('.menu_body').clone() };
    }
    hover_object.qtip({
        overwrite: false, // Make sure the tooltip won't be overridden once created
        content: q_content,
        show: {
            event: event.type, // Use the same show event as the one that triggered the event handler
            ready: true, // Show the tooltip as soon as it's bound, vital so it shows up the first time you hover!
            effect: false,
            solo: true,
        },
        hide: {
            event: "mouseleave",
            fixed: true,
            effect: false,
            delay: 100,
        },
        position: {
            viewport: $(window),
            at: "left bottom",
            my: "left top",
            adjust: {
                method: 'flip',
            },
            effect: false,
        },
        style: {
            classes: css_classes,
            tip: false,
            def: false,
        },
        events: {
            show: function(event, api) {
                api.elements.target.addClass('selected');
            },
            hide: function(event, api) {
                api.elements.target.removeClass('selected');
            },
        },
    }, event);
}


/*  User tag methods - requires an a.user_tag_link within .user_tag block. Like this:

<div class="user_tag">
  <a class="user_tag_link" href="http://link-to-action">Text</a>
</div>

*/
$(".user_tag_link").live('click', function(event) {
    try { event.preventDefault(); } catch(e) {} //For IE bugs?
    spinner().appendTo(this);
    var user_tag = $(this).parents('.user_tag');
    user_tag.load($(this).attr('href'), function(response, status, xhr) {
        if (status == 'error') {
            flash_message(voteit.translation['error_loading'], 'error');
        }
    });
    user_tag.find('.spinner').remove()
});

/* Minimize
 * Structure to make minimize work. elem can be most html tags
 * <elem id="something_unique" class="toggle_area toggle_closed"> <!--or toggle_opened -->
 *   <elem class="toggle_minimize">Something clickable</elem> <!-- if this allso has the class reload the page is reloaded after maximizing
 *   <elem class="minimizable_area">Stuff that will be hidden</elem>
 *   <elem class="minimizable_inverted">Stuff that will only be visible when it's minimized</elem>
 * </elem>
 */
$('.toggle_minimize').live('click', function(event) {
    try { event.preventDefault(); } catch(e) {}
    min_parent = $(this).parents('.toggle_area');
    // set cookie for opened or closed
    var cookie_id = min_parent.attr('id');
    if($(this).hasClass('reload')) {
        if (min_parent.hasClass('toggle_opened')) {
            $.cookie(cookie_id, 1, { expires: 7, path: '/'});
        } else {
            $.cookie(cookie_id, null, { expires: 7, path: '/'});
            location.reload();
        }
    }
    // Set parent class as opened or closed
    min_parent.toggleClass('toggle_opened').toggleClass('toggle_closed');
})
/* loading proposal and discussion forms with ajax */
$(document).ready(function() {
    $("a.proposal_button").live('click', function(event) {
        /* IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}
        
        var url = $(this).attr('href');
        $(this).parent('.inline_add_form').load(url, function(response, status, xhr) {
            if (status == "error") {
                var msg = "Sorry but there was an error: ";
                $(this).html(msg + xhr.status + " " + xhr.statusText);
                $(this).addClass('dummy-error')
            } else {
                var txtar = $(this).find("textarea");
                txtar.focus();
                txtar.caretToEnd();
                txtar.autoResizable();
            }
        });
    });
});
$(document).ready(function() {
    $("a.dummy-textarea").live('click', function(event) {
        /* IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}
        
        var url = $(this).attr('href');
        $(this).parents('.inline_add_form').load(url, function(response, status, xhr) {
            if (status == "error") {
                var msg = "Sorry but there was an error: ";
                $(this).find("div.dummy-textarea").html(msg + xhr.status + " " + xhr.statusText);
                $(this).find("div.dummy-textarea").addClass('dummy-error')
            } else {
                var txtar = $(this).find("textarea");
                txtar.focus();
                txtar.caretToStart();
                txtar.autoResizable();
            }
        });
    });
});

/* Action to mark content as read */
$(document).ready(function() {
    var url_config = $("#js_config a[name=current_url]");
    if (url_config.length > 0) {
        var url = url_config.attr('href') + '/_mark_read';
        var unread_names = [];
        $("#main .unread").each( function() {
            unread_names.push( $(this).attr('name') );
        });
        if (unread_names.length > 0) {
            $.ajax({url: url,
                    dataType: 'json',
                    data: {'unread': unread_names},
                    type: 'POST',
                    success: function(data) {
                        $.each(data, function(key, val) {
                            // Key should be either error or marked_read
                            if (key == 'error') {
                                //Do things with error
                                //FIXME: Exception view for js might be a good idea?
                                console.log(val);
                            };
                            if ((key == 'marked_read') && (val != unread_names.length)) {
                                console.log('Wrong number of marked read count returned.');
                                console.log('Requested: ' + unread_names.length + ' Returned: ' + val);
                            };
                        });
                    },
            });
        }
    };
});

/* Read more discussion post */
$(document).ready(function() {
    $(".more a").live('click', function(event) {
        /* IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}
        var url = $(this).attr('href');
        var body = $(this).parents('.listing_block').find('.body');
        var link = $(this)
        $.getJSON(url, function(data) {
            body.empty().append(data['body']);
            link.hide();
        });
    });
});

/* Show denied proposals on closed polls */
// FIXME: Class names collide with icons + need way to close again
// This code has nothing to do with this package either, but with schulze
/*
$('#proposals .show_denied a').live('click', function(event) {
    try { event.preventDefault(); } catch(e) {}
    var poll = $(this).parents("div.listing_block.poll");
       poll.find('.result div.denied').toggle();
       $(this).toggle();
});
*/

/* show previous posts */
$(document).ready(function() {
    $('#discussions div.load_more a').live('click', function(event) {
        /* stops normal events function 
        IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}
        
        $("#discussions .posts .listing").empty();
        $("#discussions .posts .listing").append(voteit.translation['loading']);
        
        var url = $(this).attr('href');
        $("#discussions .posts .listing").load(url, function(response, status, xhr) {
            if (status == "error") {
                $("#discussions .posts .listing").empty();
                $("#discussions .posts .listing").append(voteit.translation['error_loading']);
            }
        });
    });
});

/* tag filtering */
$(document).ready(function() {
    $('#proposals a.tag, #discussions a.tag, .tag_stats a').live('click', function(event) {
        /* stops normal events function 
        IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}
        
        $("#proposals .listing").empty();
        $("#proposals .listing").append(voteit.translation['loading']);
        $("#discussions .inline_add_form").empty();
        
        $("#discussions .listing").empty();
        $("#discussions .listing").append(voteit.translation['loading']);
        $("#discussions .inline_add_form").empty();
        
        var url = $(this).attr('href');
        var title = $(this).attr('title');
        $.ajax({
               url: url,
            success: function(response) {
                //pushState doesn't work on IE 8, perhaps others
                try { window.history.pushState(null, title, url); } catch(e) {}
                $('#proposals .listing').html($('#proposals .listing', response).html());
                $('#proposals .inline_add_form').html($('#proposals .inline_add_form', response).html());
                $('#discussions .listing').html($('#discussions .listing', response).html());
                $('#discussions .inline_add_form').html($('#discussions .inline_add_form', response).html());
            },
            error: function(response) {
                $("#proposals .listing").empty();
                $("#proposals .listing").append(voteit.translation['error_loading']);
                
                $("#discussions .listing").empty();
                $("#discussions .listing").append(voteit.translation['error_loading']);
            }
        });
    });
});

