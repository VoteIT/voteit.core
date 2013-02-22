/* Generic popups, not modal */

$('a.inlineinfo').live('click', function(event) {
    voteit_inline_info(event, 'inline_info');
});

$('a.moretag').live('click', function(event) {
    voteit_inline_info(event, 'inline_more');
});

function voteit_inline_info(event, css_classes) {
    try { event.preventDefault(); } catch(e) {};
    var target = $(event.currentTarget);
    target.qtip({
        overwrite: false, // Make sure the tooltip won't be overridden once created
        content: { 
           title: {
                text: voteit.translation['user_info'],
                button: voteit.translation['close'],
            },
            text: voteit.translation['loading'], // The text to use whilst the AJAX request is loading
            ajax: { 
                url: target.attr('href'),
            },
        },
        show: {
            event: event.type, // Use the same show event as the one that triggered the event handler
            ready: true,
            effect: false,
        },
        hide: {
            event: "unfocus",
            effect: false,
        },
        position: {
            viewport: $(window),
            at: "bottom center",
            my: "top center",
            adjust: {
                method: 'shift none',
            },
        },
        style: { 
            classes: 'popup popup_dropshadow ' + css_classes,
            widget: true,
            tip: true,
        },
    }, event);

}

/* answer popup */
$('a.answer').live('click', function(event) {
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
                    var txtar = $(this.elements.content).find('textarea');
                    txtar.autoResizable();
                    txtar.focus();
                    txtar.caretTo(':', 2);
                }
            }
        },
        show: {
            event: event.type, // Use the same show event as the one that triggered the event handler
            ready: true, // Show the tooltip as soon as it's bound, vital so it shows up the first time you hover!
            effect: false,
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
            classes: "answer-popup popup popup_dropshadow inline_add_form", //popup class is general
            widget: true,
            width: 358, // Exact same as columns!
        },
    }, event);
});
