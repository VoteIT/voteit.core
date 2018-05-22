
(function($) {
    //Scroll extension
    $.fn.goTo = function() {
        $('html, body').animate({
            scrollTop: $(this).offset().top - 200 + 'px'
        }, 'fast');
        return this; // for chaining...
    }

/* FIXME
    $.fn.linkHashtag = function(insert) {
        var insert = (typeof insert == 'undefined') ? '$1<a data-tag-filter="$2" href="$2">$2</a>' : insert;
        //var pattern = '/(^|\W)(#[a-z\d][\w-]*)/ig';
        //var pattern2 = '(?<=\s|^)#(\w*[A-Za-z_]+\w*)'
        //$(this).html( $(this).html().replace(/(^|\W)(#[a-z\d][\w-]*)/ig, insert) );
        //$(this).html( $(this).html().replace(/(\W+)(#[a-z\d][\w-]*)/ig, insert) );
        $(this).html( $(this).html().replace(/(^|\s)(#[a-z\d-]+)/ig, insert) );
    }
    */

})(jQuery);


/* Main configuration */
if(typeof(voteit) == "undefined"){
    voteit = {};
}

/* Prioritize displaying flash messages in voteits area that floats under the menu */
arche.flash_slot_order = ['modal', 'voteit-context-actions', 'voteit-main', 'main'];

function adjust_column_size(event) {
    // We may want to make this function smarter later on
    var clicked = $(event.currentTarget);
    clicked.goTo();
    $('[data-resize-btn]').toggleClass('hidden');
    var targets = $('[data-main-col-resize]').toggleClass('col-sm-6 col-sm-12');
}


$(function() {
    /* Internet Explorer not supported */
    var is_ie = window.navigator.userAgent.indexOf("MSIE ") > 0 || !!navigator.userAgent.match(/Trident.*rv\:11\./);
    if (is_ie) {
        arche.create_flash_message(
            "You seem to be using Internet Explorer. Please switch browser, " +
            "since IE is no longer being maintained by its authors. This site (and many others) " +
            "won't function correctly with IE.",
            {icon_class: 'glyphicon glyphicon-warning-sign', type: 'danger', auto_destruct: false}
        );
    }

    $('body').on('click', '[data-resize-btn]', adjust_column_size);
});

