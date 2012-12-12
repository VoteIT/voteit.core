
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