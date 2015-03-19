/* VoteIT deform fixes */


/* FIXME: Kept as a reference, but do check these files. */

/* deform ajax success callback */
function voteit_deform_success(rText, sText, xhr, form) {
	var url = xhr.getResponseHeader('X-Relocate');
	if (url) {
		window.location.assign(url);
	} else {
		deform.processCallbacks();
		deform.focusFirstInput();
	}
}

function voteit_poll_error(xhr, status, error, id) {
	deform.processCallbacks();
	deform.focusFirstInput();
	var button = $('form.deform', xhr.responeText).find('li.buttons button');
	var message = $('form.deform', xhr.responeText).parents('.booth.poll').find('.error.message');
	message.empty();
	if(status=='timeout') {
        message.append(voteit.translation['voting_timeout_msg']);
        button.removeAttr("disabled");
    } 
	else
		message.append(voteit.translation['voting_error_msg']);
	message.insertBefore(button);
	message.fadeIn(3000);
	var button = $(id+" .booth.poll").find('form.deform li.buttons');
	button.find('img').remove();
}

function voteit_poll_beforeSubmit(arr, form, options) {
	var button = form.find('button[type=submit]');
	button.attr("disabled", "disabled");
	spinner().insertAfter(button.find('span'));
	$(form).parents('.booth.poll').find('.success.message').hide();
	$(form).parents('.booth.poll').find('.error.message').hide();
} 

function voteit_poll_complete(xhr, textStatus) {
    if (xhr.status == 200) {
        $('.booth', xhr.responeText).css('width', $('#content').width()*0.7);
        var button = $('form.deform', xhr.responeText).find('li.buttons button');
        var message = $('form.deform', xhr.responeText).parents('.booth.poll').find('.success.message');
        message.insertBefore(button);
        message.fadeIn(3000);
    } else {
        window.location.reload();
    }
}