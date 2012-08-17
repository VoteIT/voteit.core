/* VoteIT deform fixes */

/* Show description
 * This is kind of a hack - what we really want is for deform to start
 * displaying description texts. They're open to that idea if we submit
 * a patch to them. /Robin */
function display_deform_labels() {
    $('label.desc').each(function() {
        var desc = $(this).attr('title');
        if(desc != '')
            $(this).after('<p>'+desc+'</p>');
            $(this).attr('title', '');
    });
}
$(document).ready(function() {
    display_deform_labels();
});

/* changin end time for polls when start time changes */
var start_end_time_diff = 0;
$(document).delegate('input[name="start_time"]', 'focus', function() {
	// get the dates
	var start_time = $('input[name="start_time"]').datepicker("getDate")
	var end_time = $('input[name="end_time"]').datepicker("getDate")
	
	// calculate the differens
	var new_start_end_time_diff = new Date(end_time).getTime() - new Date(start_time).getTime();
	if(new_start_end_time_diff > 0)
		start_end_time_diff = new_start_end_time_diff;
});

$(document).delegate('input[name="start_time"]', 'change', function() {
	// get the dates
	var start_time = $('input[name="start_time"]').datepicker("getDate")
	var ds = new Date(start_time);
	
	// set new end time
	var de = new Date();
	de.setTime(ds.getTime() + start_end_time_diff);
	
	end_time = de.getFullYear() + '-' + 
			   ('0' + (de.getMonth()+1)).slice(-2) + '-' + 
			   ('0' + de.getDate()).slice(-2) + ' ' + 
			   ('0' + de.getHours()).slice(-2) + ':' + 
			   ('0' + de.getMinutes()).slice(-2);
	
	$('input[name="end_time"]').val(end_time);
	$('input[name="end_time"]').datepicker("setDate", de);
});

/* deform ajax success callback */
function voteit_deform_success(rText, sText, xhr, form) {
	var url = xhr.getResponseHeader('X-Relocate');
	if (url) {
		document.location = url;
		window.location.reload(true)
	} else {
		deform.processCallbacks();
		deform.focusFirstInput();
	}
}