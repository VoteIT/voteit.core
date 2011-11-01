/* JS that should be present on every page, regardless of its function.*/
var voteit = {};
voteit.translation = {};

/* Translations loader. This must be loaded before all other voteit js! */
$(document).ready(function () {
	$('.voteit_js_translation').each(function () {
		$(this).children().each(function() {
			item = $(this);
			tkey = item.attr('class').replace('js_trans_', '');
			voteit.translation[tkey] = item.text();
		});
	});
});

/* Flash messages */
$(document).ready(function () {
    $('#flash_messages .close_message').live('click', function(event) {
        //Parent of the .close_message class should be .message
        $(this).parent().slideUp(200);
    });
});

/* Menus
 * example layout:
 * <div class="dropdown_menu">
 *   <a class="menu_header">x</a>
 *   <div class="menu_body">Dropdown menu here</a>
 * </div>
 */
$(document).ready(function () {
    $('#meeting-actions .dropdown_menu .menu_header').live('click', function(event) {
        return false;
    });
    $('#meeting-actions .dropdown_menu').hover(
        function () {
            //show its submenu
            $(this).find('.menu_body').slideDown(100);
            $(this).find('.menu_header').addClass('hover');
        },
        function () {
            //hide its submenu
            $(this).find('.menu_body').slideUp(100);
            $(this).find('.menu_header').removeClass('hover');
        }
    );
});

$('#navigation .dropdown_menu').live('hover', display_qtip_menu);
$('#main_window .dropdown_menu').live('hover', display_qtip_menu);

function display_qtip_menu(event) {
    /* stop form from submitting normally 
    IE might throw an error calling preventDefault(), so use a try/catch block. */
    try { event.preventDefault(); } catch(e) {}
    event.preventDefault(); 
    
    $(this).qtip({
        overwrite: false, // Make sure the tooltip won't be overridden once created
        content: { 
            text: $(this).find('.menu_body'), // The text to use whilst the AJAX request is loading
        },
        show: {
            event: event.type, // Use the same show event as the one that triggered the event handler
            ready: true, // Show the tooltip as soon as it's bound, vital so it shows up the first time you hover!
            effect: false,
        },
        hide: {
            event: "mouseleave",
            fixed: true,
            effect: false,
        },
        position: {
            viewport: $(window),
            at: "right center",
            my: "left top",
            adjust: {
                method: 'flip',
            }
        },
        style: { 
            classes: "qtip_menu"
        },
    }, event);
}

/*  User tag methods */
$(document).ready(function() {
    $(".user_tag_form").live('submit', function(event) {
        /* stop form from submitting normally 
        IE might throw an error calling preventDefault(), so use a try/catch block. */
        try { event.preventDefault(); } catch(e) {}
        /* get some values from elements on the page: */
        var $form = $( this ),
            tag = $form.find('input[name="tag"]').val(),
            _do = $form.find('input[name="do"]').val(),
            display_name = $form.find('input[name="display_name"]').val(),
            expl_display_name = $form.find('input[name="expl_display_name"]').val(),
            url = $form.attr('action'),
            id = $form.parent().attr('id');
        /* Send the data using post and put the results in a div */
        $.post(url, {'tag': tag, 'do': _do, 'display_name': display_name, 'expl_display_name':expl_display_name},
          function(data) {
              $("#"+id).html(data);
          }
        );
    });
});
/* Minimize
 * Structure to make minimize work. elem can be most html tags
 * <elem id="something_unique" class="toggle_area toggle_closed"> <!--or toggle_opened -->
 *   <elem class="toggle_minimize">Something clickable</elem>
 *   <elem class="minimizable_area">Stuff that will be hidden</elem>
 *   <elem class="minimizable_inverted">Stuff that will only be visible when it's minimized</elem>
 * </elem>
 */
$(document).ready(function() {
    $('#navigation .toggle_minimize').live('click', function(event) {
        min_parent = $(this).parents('.toggle_area');
        // set cookie for opened or closed
        var cookie_id = min_parent.attr('id');
        if (min_parent.hasClass('toggle_opened')) {
            $.cookie(cookie_id, 1);
        } else {
            $.cookie(cookie_id, null);
            location.reload();
        }
        // Set parent class as opened or closed
        min_parent.toggleClass('toggle_opened').toggleClass('toggle_closed');
    })
});


//FIXME: Refactor minimize. It's sensless to have two methods that does alsmost
//the same thing and are hardcoded to a specific id.


/* Poll result */
$(document).ready(function() {
    $('#polls .toggle_minimize').live('click', function(event) {
        min_parent = $(this).parents('.toggle_area');
        // set cookie for opened or closed
        var cookie_id = min_parent.attr('id');
        if (min_parent.hasClass('toggle_opened')) {
            $.cookie(cookie_id, 1);
        } else {
            $.cookie(cookie_id, null);
        }
        // Set parent class as opened or closed
        min_parent.toggleClass('toggle_opened').toggleClass('toggle_closed');
    })
});
