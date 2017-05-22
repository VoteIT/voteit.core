
(function($) {
    //Scroll extension
    $.fn.goTo = function() {
        $('html, body').animate({
            scrollTop: $(this).offset().top - 100 + 'px'
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
arche.flash_slot_order = ['modal', 'voteit-main', 'main'];
