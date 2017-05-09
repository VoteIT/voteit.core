
//Scroll extension
(function($) {
    $.fn.goTo = function() {
        $('html, body').animate({
            scrollTop: $(this).offset().top - 100 + 'px'
        }, 'fast');
        return this; // for chaining...
    }
})(jQuery);

/* Main configuration */
if(typeof(voteit) == "undefined"){
    voteit = {};
}

/* Prioritize displaying flash messages in voteits area that floats under the menu */
arche.flash_slot_order = ['modal', 'voteit-main', 'main'];


voteit.toggle_nav = function(selector) {
    //$(selector).toggleClass('activated');
    if ($(selector).hasClass('activated')) {
        voteit.hide_nav(selector);
    } else {
        voteit.show_nav(selector);
    }
}


voteit.show_nav = function(selector) {
/*
    var out = '<a id="fixed-nav-backdrop" href="javascript:voteit.hide_nav(';
    out += "'" + selector + "'";
    out += ')" />';
    if ($('#fixed-nav-backdrop').length == 0) $('body').append($(out));
    */
    $(selector).addClass('activated');
    $('#fixed-nav-backdrop').data('active-menu', selector);
    $('#fixed-nav-backdrop').fadeIn();
}


voteit.hide_nav = function(selector) {
    var selector = (typeof selector == 'string') ? selector : $('#fixed-nav-backdrop').data('active-menu');
    $(selector).removeClass('activated');
    $('#fixed-nav-backdrop').fadeOut();
    $('#fixed-nav-backdrop').data('active-menu', null);
}