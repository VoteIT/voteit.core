/* Agenda Item common JS */
/* more tag popup */
$('a.moretag').live('click', function(event) {
    /* stop form from submitting normally 
    IE might throw an error calling preventDefault(), so use a try/catch block. */
    try { event.preventDefault(); } catch(e) {}
    event.preventDefault(); 
    $(this).qtip({
        overwrite: false, // Make sure the tooltip won't be overridden once created
                content: { 
           title: {
                text: voteit.translation['more_tag_list'],
                button: voteit.translation['close'],
            },
            text: voteit.translation['loading'], // The text to use whilst the AJAX request is loading
            ajax: { 
                url: this.href,
            },
        },
        show: {
            event: event.type, // Use the same show event as the one that triggered the event handler
            ready: true, // Show the tooltip as soon as it's bound, vital so it shows up the first time you hover!
            effect: false,
        },
        hide: {
            event: "unfocus",
            effect: false,
        },
        position: {
            at: "bottom center",
            my: "top center",
        },
        style: { 
            classes: 'moretag-popup',
            widget: true,
            tip: true,
        },
    }, event);
});

//FIXME: This is almost the same as the moretag. Seems silly to duplicate.
/* profile popup */
$('a.inlineinfo').live('click', function(event) {
    /* stop form from submitting normally 
    IE might throw an error calling preventDefault(), so use a try/catch block. */
    try { event.preventDefault(); } catch(e) {}
    event.preventDefault(); 
    
    $(this).qtip({
        overwrite: false, // Make sure the tooltip won't be overridden once created
        content: { 
           title: {
                text: voteit.translation['user_info'],
                button: voteit.translation['close'],
            },
            text: voteit.translation['loading'], // The text to use whilst the AJAX request is loading
            ajax: { 
                url: this.href,
            },
        },
        show: {
            event: event.type, // Use the same show event as the one that triggered the event handler
            ready: true, // Show the tooltip as soon as it's bound, vital so it shows up the first time you hover!
            effect: false,
        },
        hide: {
            event: "unfocus",
            effect: false,
        },
        position: {
            at: "bottom center",
            my: "top center",
        },
        style: { 
            classes: 'inlineinfo-popup',
            widget: true,
            tip: true,
        },
    }, event);
});
