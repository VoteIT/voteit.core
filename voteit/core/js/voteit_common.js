/* JS that should be present on every page, regardless of its function.*/
var voteit = {};
voteit.translation = {};

/* Translations loader. This must be loaded before all other voteit js! */
$(document).ready(function () {
    $('.voteit_js_translation').each(function () {
        $(this).children().each(function() {
            var item = $(this);
            var tkey = item.attr('class').replace('js_trans_', '');
            voteit.translation[tkey] = item.text();
        });
    });
});

/* Flash messages */
$(document).ready(function () {
    $('#flash_messages .close_message').live('click', function(event) {
        //Parent of the .close_message class should be .message
        $(this).parent().slideUp(200);
    });
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
        },
        hide: {
            event: "mouseleave",
            fixed: true,
            effect: false,
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
    $("a.dummy-textarea").live('click', function(event) {
        /* IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}
        
        var url = $(this).attr('href');
        $(this).parent('.inline_form_placeholder').load(url, function(response, status, xhr) {
            if (status == "error") {
                var msg = "Sorry but there was an error: ";
                $(this).find("div.dummy-textarea").html(msg + xhr.status + " " + xhr.statusText);
                $(this).find("div.dummy-textarea").addClass('dummy-error')
            } else {
                var txtar = $(this).find("textarea");
                txtar.focus();
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
        $(".unread").each( function() {
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
                     }
            });
        }
    };
});


// Contact & Support tab
$(document).ready(function() {
    $('#help-tab > h5').qtip({
        content: { 
            title: {
                text: voteit.translation['help_contact'],
                button: true,
            },
            text: $("#help-tabs"),
        },
        show: {
            event: "click",
            modal: true,
        },
        hide: {
            event: false,
        },
        position: {
            my: 'center',
            at: 'center',
            target: $(document.body),
        },
        style: {
            classes: "help-modal",
            width: "400px",
            height: "400px",
        },
    });
});

$(document).ready(function() {
    $("#help-tabs > ul a.tab").click(function(event) {
        /* IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}
        
        $(this).parents("#help-tabs").find("a.tab").removeClass("active");
        $(this).addClass("active");
        
        url = $(this).attr("href");
        
        $("#help-tabs .tabs").load(url, function(data) {
            $("#help-tabs .tabs form").attr('href') = url;
        });
    });

    $("#help-tabs form").live("submit", function() {
        $.post($(this).attr('action')),
            { send: 'send', subject: $(this).find("input[name='subject']").val(), message: $(this).find("textarea").val() },
            function(data) {
                $("#help-tabs .tabs").empty();
                $("#help-tabs .tabs").append(data);
            }
      });
});
