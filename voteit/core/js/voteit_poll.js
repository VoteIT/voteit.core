
/* Open poll booth when poll buttons is pressed*/
$('.open_poll_button').live('click', function(event) {
    try { event.preventDefault(); } catch(e) {}

    var button = $(this);
    spinner().appendTo(button);

    var poll = $(this).parents(".poll");
    var id = $(poll).attr('id');
    var url = button.attr('href');
    var booth_wrapper = $('<div class="booth_wrapper">');
    $(booth_wrapper).attr('id', 'booth_'+id);
    $(booth_wrapper).appendTo('#main');
    $(booth_wrapper).position({
        of: $(poll),
        my: "left top",
        at: "left top",
        collision: "none none",
    });
    $(booth_wrapper).load(url, function(response, status, xhr) {
        if (status == "error") {
            flash_message("Sorry but there was an error loading poll: " + xhr.status + " " + xhr.statusText, 'error', true);
            booth_wrapper.remove();
        } else {
            apply_mask(false);
            deform.processCallbacks();
            display_deform_labels();
        }
        button.find('img.spinner').remove();
    });
});

//Submitting the actual vote
$('#vote_form button.submit').live('click', function(event) {
    try { event.preventDefault(); } catch(e) {};
    var button = $(this);
    spinner().appendTo(button);
    var form = button.parents('form')
    var form_data = form.serialize();
    var target = form.parents('.vote_form_area');
    form_data += '&vote=1'; //XXX Hack to make sure add is in there
    $.post(form.attr('action'), form_data, function(data, status, xhr) {
        //Update with response data
        target.empty();
        target.html(data);
        deform.processCallbacks();
        display_deform_labels();
    })
    .error(function(xhr, status, error) {
        button.find('img.spinner').remove();
        flash_message('Server error', 'error', true);
    });
})

/* close booth when close button is clicked
 * 
 *FIXME: This html is now removed, i don't know if i want to readd it since it conflicts with cogwheel for moderators.
$('.booth.poll a.close').live('click', function(event) {
    try { event.preventDefault(); } catch(e) {}
    var booth_wrapper = $(this).parents(".booth_wrapper");
    booth_wrapper.remove();
    remove_mask();
});
*/

//Remove if mask area is clicked - this might not be a good idea to keep
$('#mask').click(function() {
    $(".booth_wrapper").remove();
    remove_mask();
});

//Remove if esc is pressed
$(document).keyup(function(e) {
    if(e.keyCode == 27) {
        $(".booth_wrapper").remove();
        remove_mask();
    }
});

/* Masking */
function apply_mask($prevent_scrolling) {
    //Prevent the page from scrolling
    $prevent_scrolling = typeof $prevent_scrolling !== 'undefined' ? $prevent_scrolling : true;
    if($prevent_scrolling)
        $("body").css("overflow", "hidden");
    //Get the screen height and width
    var maskHeight = $(document).height();
    var maskWidth = $(document).width();
    //Set height and width to mask to fill up the whole screen
    var mask = $('#mask');
    if (mask.length == 0) {
        $('<div class="booth_wrapper">').appendTo('body');
        mask = $('#mask');
    }
    $('#mask').css({'width':maskWidth,'height':maskHeight});
    //transition effect
    $('#mask').fadeTo("slow", 0.3);
}
function remove_mask() {
    $('#mask').hide();
    $("body").css("overflow", "auto");
}


/*
//$(window).resize(reapply_mask);
//$(window).scroll(reapply_mask);
function reapply_mask() {
    //Get the screen height and width
    var maskHeight = $(document).height();
    var maskWidth = $(window).width();
    //Set height and width to mask to fill up the whole screen
    $('#mask').css({'width':maskWidth,'height':maskHeight});
}
*/