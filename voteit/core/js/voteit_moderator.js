
/* Cogwheel menus */
$('.cogwheel').live('hover', function(event) {
    /* stop form using default action 
    IE might throw an error calling preventDefault(), so use a try/catch block. */
    try { event.preventDefault(); } catch(e) {}
    if ($(this).hasAttr('url')) {
        var url = $(this).attr('url');
        var q_content = { 
            text: voteit.translation['loading'], // The text to use whilst the AJAX request is loading
            ajax: {
                url: url,
            }
        };
    }
    else {
        //We need a copy of the content, otherwise qtip will try to locate it every time it triggers
        var q_content = { text: $(this).parent().find('.menu_body').clone() };
    }
    $(this).qtip({
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
            at: "right center",
            my: "left center",
            adjust: {
                method: 'flip',
            },
            effect: false
        },
        style: {
            classes: "qtip_menu",
            tip: false,
        },
    }, event);
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
