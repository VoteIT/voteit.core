function open_modal_window(obj) {
	//Get the screen height and width
    var maskHeight = $(document).height();
    var maskWidth = $(document).width();
 
    //Set height and width to mask to fill up the whole screen
    $('#modal-mask').css({'width':maskWidth,'height':maskHeight});
     
    //transition effect  
    $('#modal-mask').fadeTo("slow", 0.8);
 
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
        $('#modal-mask, .modal-window').hide();
    });     
     
    //if mask is clicked
    $('#modal-mask').click(function () {
        $(this).hide();
        $('.modal-window').hide();
    });
});

$(document).ready(function () {
	$(window).resize(recalc_modal_placement);
	$(window).scroll(recalc_modal_placement);
});

function recalc_modal_placement() { 
    //Get the screen height and width
    var maskHeight = $(document).height();
    var maskWidth = $(window).width();
  
    //Set height and width to mask to fill up the whole screen
    $('#modal-mask').css({'width':maskWidth,'height':maskHeight});
           
    //Get the window height and width
    var winH = $(window).height();
    var winW = $(window).width();
    
    var scrollT = $(window).scrollTop();
    var scrollL = $(window).scrollLeft();
            
    //Set the popup window to center
    $(".modal-window").css('top',  Math.round(winH/2-$(".modal-window").outerHeight()/2+scrollT));
    $(".modal-window").css('left', Math.round(winW/2-$(".modal-window").outerWidth()/2+scrollL));
}

$(document).keyup(function(e) {
	if(e.keyCode == 27) {
		$('#modal-mask').hide();
		$('.modal-window').hide();
	}
});