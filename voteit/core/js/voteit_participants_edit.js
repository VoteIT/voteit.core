$(document).ready(function () {
    $('.submit_participants_form').live('click', function(event) {
        try { event.preventDefault(); } catch(e) {};
        var button = this;
        spinner().appendTo(button);
        var form = $(this).parents('form');
        link = $(this).attr('href');
        $.post(link, $(form).serialize(), function(data, textStatus, jqXHR) {
            load_participants_data();
        })
        .success(function() { 
        	$(button).find('img.spinner').remove();
        	flash_message(voteit.translation['permssions_updated_success'], 'info', true); 
    	})
    	.error(function() {
    		$(button).find('img.spinner').remove(); 
    		flash_message(voteit.translation['permssions_updated_error'], 'error', true); 
		});
    });
    $('.role').live('click', function(event) {
        try { event.preventDefault(); } catch(e) {};
        if ($(this).hasClass('read_only') == true) {
            alert("Can't change admin permission here!");
            return false;
        }
        toggle_checked_roles(this);
    });
    $('.check_all').live('click', check_all);
    $('.uncheck_all').live('click', uncheck_all);
});


function toggle_checked_roles(role_elem) {
    var role_elem = $(role_elem);
    role_elem.toggleClass('changed');
    var checkbox = $(role_elem).find('input');
    if (checkbox.attr('checked') == 'checked') {
        var out = $('#listing_templates .no_icon').clone();
        checkbox.removeAttr('checked');
    }
    else {
        var out = $('#listing_templates .yes_icon').clone();
        checkbox.attr('checked', true);
    }
    role_elem.find('.graphic_checkbox').replaceWith(out);
}

function check_all(event) {
    try { event.preventDefault(); } catch(e) {};
    var role_selector = '.'+$(this).parents('th.toggle_all').attr('name');
    $(role_selector).each(function () {
        if ($(this).find('input').attr('checked') != 'checked') {
            toggle_checked_roles(this);
        }
    });
}
function uncheck_all(event) {
    try { event.preventDefault(); } catch(e) {};
    var role_selector = '.'+$(this).parents('th.toggle_all').attr('name');
    $(role_selector).each(function () {
        if ($(this).find('input').attr('checked') == 'checked') {
            toggle_checked_roles(this);
        }
    });
}
