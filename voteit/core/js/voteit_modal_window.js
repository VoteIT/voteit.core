/* Modal window code. Currently not used, and somewhat broken. 
 * Please check properly and rewrite if it needs to be used.
 * It might be a better idea to use qTips modal verison, like poll booth. */

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