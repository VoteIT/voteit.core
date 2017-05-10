
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
