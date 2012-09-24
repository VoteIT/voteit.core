$.ajaxSetup ({
	cache: false
});

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
    var div = $('#flash_messages');
    if(div) {
        var start = $(div).offset().top;
     
        $.event.add(window, "scroll", function() {
            var p = $(window).scrollTop();
            $(div).css('position',((p)>start) ? 'fixed' : 'static');
            $(div).css('top',((p)>start) ? '0px' : '');
        });
   }
});

$('.cogwheel .menu_header').live('hover', display_cogwheel_menu);
function display_cogwheel_menu(event) {
    /* stop form from submitting normally 
    IE might throw an error calling preventDefault(), so use a try/catch block. */
    try { event.preventDefault(); } catch(e) {}
    $(this).qtip({
        overwrite: false, // Make sure the tooltip won't be overridden once created
        content: { 
            text: $(this).parent().find('.menu_body'), // The text to use whilst the AJAX request is loading
        },
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
            at: "right center",
            my: "left center",
            adjust: {
                method: 'flip',
            }
        },
        style: {
            classes: "qtip_menu cogwheel-body",
        },
    }, event);
}

$('#meeting-actions-menu .dropdown_menu').live('hover', display_meeting_menu);
function display_meeting_menu(event) {
    /* stop form from submitting normally 
    IE might throw an error calling preventDefault(), so use a try/catch block. */
    try { event.preventDefault(); } catch(e) {}
    
    $(this).qtip({
        overwrite: false, // Make sure the tooltip won't be overridden once created
        content: { 
            text: $(this).find('.menu_body'), // The text to use whilst the AJAX request is loading
        },
        show: {
            event: event.type, // Use the same show event as the one that triggered the event handler
            ready: true, // Show the tooltip as soon as it's bound, vital so it shows up the first time you hover!
            effect: false,
        },
        hide: {
            event: "mouseleave",
            fixed: true,
            effect: false,
        },
        position: {
            viewport: $(window),
            at: "right bottom",
            my: "right top",
            adjust: {
                method: 'flip',
            }
        },
        style: {
            classes: "qtip_menu meeting-menu-body",
        },
    }, event);
}

$('#meeting-actions-menu .dropdown_menu_poll').live('hover', display_meeting_menu_poll);
function display_meeting_menu_poll(event) {
    /* stop form from submitting normally 
    IE might throw an error calling preventDefault(), so use a try/catch block. */
    try { event.preventDefault(); } catch(e) {}
    
    var url = $(this).attr('url');
    $(this).qtip({
        overwrite: false, // Make sure the tooltip won't be overridden once created
        content: { 
            text: voteit.translation['loading'], // The text to use whilst the AJAX request is loading
            ajax: {
                url: url,
            }
        },
        show: {
            event: event.type, // Use the same show event as the one that triggered the event handler
            ready: true, // Show the tooltip as soon as it's bound, vital so it shows up the first time you hover!
            effect: false,
        },
        hide: {
            event: "mouseleave",
            fixed: true,
            effect: false,
        },
        position: {
            viewport: $(window),
            at: "right bottom",
            my: "right top",
            effect: false,
            adjust: {
                method: 'flip',
            }
        },
        style: {
            classes: "qtip_menu meeting-menu-body",
        },
    }, event);
}

/*  User tag methods */
$(document).ready(function() {
    $(".user_tag_form").live('submit', function(event) {
        /* stop form from submitting normally 
        IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}

        /* get some values from elements on the page: */
        var $form = $( this ),
            tag = $form.find('input[name="tag"]').val(),
            _do = $form.find('input[name="do"]').val(),
            display_name = $form.find('input[name="display_name"]').val(),
            expl_display_name = $form.find('input[name="expl_display_name"]').val(),
            url = $form.attr('action'),
            id = $form.parent().attr('id');
        /* Send the data using post and put the results in a div */
        $.post(url, {'tag': tag, 'do': _do, 'display_name': display_name, 'expl_display_name':expl_display_name},
          function(data) {
              $("#"+id).html(data);
          }
        );
    });
});
/* Minimize
 * Structure to make minimize work. elem can be most html tags
 * <elem id="something_unique" class="toggle_area toggle_closed"> <!--or toggle_opened -->
 *   <elem class="toggle_minimize">Something clickable</elem> <!-- if this allso has the class reload the page is reloaded after maximizing
 *   <elem class="minimizable_area">Stuff that will be hidden</elem>
 *   <elem class="minimizable_inverted">Stuff that will only be visible when it's minimized</elem>
 * </elem>
 */
$(document).ready(function() {
    $('.toggle_minimize').live('click', function(event) {
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
});

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
        $("#main_window .unread").each( function() {
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
    $("#discussions span.more a").live('click', function(event) {
        /* IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}
        
        var url = $(this).attr('href');
        var body = $(this).parents('div.listing_block').find('span.body');
        var link = $(this)
        $.getJSON(url, function(data) {
            body.empty().append(data['body']);
            link.hide();
        });
    });
});

/* Masking */
function apply_mask($prevent_scrolling) {
	//Prevent the page from scrolling
	$prevent_scrolling = typeof $prevent_scrolling !== 'undefined' ? $prevent_scrolling : true;
	if($prevent_scrolling)
    	$("body").css("overflow", "hidden");
    
    //Get the screen height and width
    var maskHeight = $(document).height();
    var maskWidth = $(document).width();
 
    //Set height and width to mask to fill up the whole screen
    $('#mask').css({'width':maskWidth,'height':maskHeight});
     
    //transition effect  
    $('#mask').fadeTo("slow", 0.3);
}

function remove_mask() {
	$('#mask').hide();
    $("body").css("overflow", "auto");
}

$(document).ready(function() {     
    //if mask is clicked
    $('#mask').click(function() {
        remove_mask();
    });
});

$(document).keyup(function(e) {
    if(e.keyCode == 27) {
		remove_mask();
    }
});

$(window).resize(reapply_mask);
$(window).scroll(reapply_mask);

function reapply_mask() {
    //Get the screen height and width
    var maskHeight = $(document).height();
    var maskWidth = $(window).width();
    //Set height and width to mask to fill up the whole screen
    $('#mask').css({'width':maskWidth,'height':maskHeight});
}

/* Modal window funcs */
function open_modal_window(obj) {
    apply_mask();
 
    //Get the window height and width
    var winH = $(window).height();
    var winW = $(window).width();
    
    var scrollT = $(window).scrollTop();
    var scrollL = $(window).scrollLeft();
    
    //Set the popup window to center
    $(obj).css('top',  Math.round(winH/2-$(obj).outerHeight()/2+scrollT));
    $(obj).css('left', Math.round(winW/2-$(obj).outerWidth()/2+scrollL));
 
    //transition effect
    $(obj).fadeIn(2000);
}

$(document).ready(function() {
    //if close button is clicked
    $('.modal-window .close').click(function (e) {
        //Cancel the link behavior
        e.preventDefault();
        $('.modal-window').hide();
        remove_mask();
    });
});

$(document).ready(function() {     
    //if mask is clicked
    $('#mask').click(function() {
        $('.modal-window').hide();
    });
});

$(document).keyup(function(e) {
    if(e.keyCode == 27) {
		$('.modal-window').hide();
    }
});

$(document).ready(function () {
    $(window).resize(recalc_modal_placement);
    $(window).scroll(recalc_modal_placement);
});

function recalc_modal_placement() {
    //Get the window height and width
    var winH = $(window).height();
    var winW = $(window).width();
    var scrollT = $(window).scrollTop();
    var scrollL = $(window).scrollLeft();
    //Set the popup window to center
    $(".modal-window").css('top',  Math.round(winH/2-$(".modal-window").outerHeight()/2+scrollT));
    $(".modal-window").css('left', Math.round(winW/2-$(".modal-window").outerWidth()/2+scrollL));
}

$(document).ready(function() {
    $('#help-tab > a').live('click', function(event) {
        /* stops normal events function 
        IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}
        
        open_modal_window("#help-dialog");
    });
    
    $('#help-actions a.tab').live('click', function(event) {
        /* stops normal events function 
        IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}
        
       $('#help-actions a.tab').removeClass('active');
       $(this).addClass('active'); 

        var url = $(this).attr('href');
        $("#help-dialog .content").load(url, function(response, status, xhr) {
            deform.processCallbacks();
            display_deform_labels();
        });
    });
});

/* Open poll booth when poll buttons is pressed*/
$(document).ready(function() {
    $('#proposals a.poll_booth').live('click', function(event) {
        /* stops normal events function 
        IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}
        
        var button = $(this);
        spinner().appendTo(button);
        
        var poll = $(this).parents("div.listing_block.poll");
        var id = $(poll).attr('id');  
        var url = $(this).attr('href');
        
        var booth_wrapper = $('<div class="booth_wrapper">');
        $(booth_wrapper).attr('id', 'booth_'+id);
        $(booth_wrapper).appendTo('#proposals');
        $(booth_wrapper).position({
            of: $(poll),
            my: "left top",
            at: "left top",
            collision: "none none",
        });
        $(booth_wrapper).load(url, function(response, status, xhr) {
            if (status == "error") {
                flash_message("Sorry but there was an error loading poll: " + xhr.status + " " + xhr.statusText, 'error', true);
                booth_wrapper.remove();
            } else {
                apply_mask(false);
                booth_wrapper.find('.booth').css('width', $('#content').width()*0.7);
                deform.processCallbacks();
                display_deform_labels();
            }
            button.find('img.spinner').remove();
        });
    });
});

/* close booth when close button is clicked */
$(document).ready(function() {
    $('.booth.poll a.close').live('click', function(event) {
        /* stops normal events function 
        IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}
        
        var booth_wrapper = $(this).parents(".booth_wrapper");
        booth_wrapper.remove();
        remove_mask();
    });
});

$(document).ready(function() {     
    //if mask is clicked
    $('#mask').click(function() {
        $(".booth_wrapper").remove();
    });
});

$(document).keyup(function(e) {
    if(e.keyCode == 27) {
		$(".booth_wrapper").remove();
    }
});

/* Show denied proposals on closed polls */
$(document).ready(function() {
    $('#proposals .show_denied a').live('click', function(event) {
        /* stops normal events function 
        IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}
        
        var poll = $(this).parents("div.listing_block.poll");
           poll.find('.result div.denied').toggle();
           $(this).toggle();
    });
});

/* ajaxifing show previous posts */
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

/* answer popup */
$(document).ready(function() {
    $('a.answer').live('click', function(event) {
        /* stop form from submitting normally 
        IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}

	    if($(this).parents('#proposals').length > 0)
	    	title_text = voteit.translation['answer_popup_title_comment'];
    	else
	    	title_text = voteit.translation['answer_popup_title_answer'];
	    
	    var url = $(this).attr('href');
	    $(this).qtip({
	        overwrite: false, // Make sure the tooltip won't be overridden once created
	        content: { 
	        	title: {
	        		text: title_text,
	        		button: voteit.translation['close'],
	        	},
	            text: voteit.translation['loading'], // The text to use whilst the AJAX request is loading
	            ajax: {
	                url: url,
	                success: function(data, status) {
    					this.set('content.text', data);
    					deform.processCallbacks();
    					$(this.elements.content).find('textarea').focus();
    					$(this.elements.content).find('textarea').caretTo(':', 2);
	                }
	            }
	        },
	        show: {
	            event: event.type, // Use the same show event as the one that triggered the event handler
	            ready: true, // Show the tooltip as soon as it's bound, vital so it shows up the first time you hover!
	            effect: true,
	            solo: true,
	        },
	        hide: {
	        	event: "false",
	            fixed: true,
	            effect: false,
	        },
	        position: {
	            at: "bottom center",
	            my: "top center",
	            adjust: {
	                method: 'flip',
	            }
	        },
	        style: {
	        	width: 500,
            	classes: "answer-popup",
            	widget: true,
        	},
	    }, event);
	});
});

/* ajaxifing tag filtering */
$(document).ready(function() {
    $('#proposals a.tag, #discussions a.tag').live('click', function(event) {
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
            	window.history.pushState(null, title, url);
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

/* Notify about proposals when deleting a poll */
$('.menu_body.Poll a.delete').live('click', function(event) {
    var id = $(this).parents('.menu_body').attr('id').replace('action_menu_', '');
    
    var poll = $.find('#'+id+'.notify_delete');
    if(poll.length > 0) {
    
        /* stops normal events function 
        IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}
        
        var dialog = $('<div class="dialog confirm">' + voteit.translation['delete_poll_notification_text'] + '</div>');

        $(dialog).dialog({
            autoOpen: false,
            resizable: false,
            draggable: true,
            closeOnEscape: true,
            width: 400,
            minHeight: 120,
            maxHeight: 200,
            buttons: [{
                text: voteit.translation['ok'],
                click: function() { $(this).dialog("close"); }
            }],
            title: voteit.translation['delete_poll_notification_title'],
            closeText: voteit.translation['close'],
            modal: true
        });
        
        $(dialog).dialog('open');
    }
});