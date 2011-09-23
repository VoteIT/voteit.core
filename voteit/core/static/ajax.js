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
    $('.dropdown_menu .menu_header').live('click', function(event) {
        return false;
    });
    $('.dropdown_menu').hover(
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

/*  User tag methods */
$(document).ready(function() {
    $(".user_tag_form").live('submit', function(event) {
        /* stop form from submitting normally */
        event.preventDefault(); 
            
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

/* helpbuttons */
$(document).ready(function() {
    $('a.help').each(function() {
        $(this).click(function() {
            return false;
        });
        $(this).qtip({
            content: { url: this.href },
            show: 'click',
            hide: 'unfocus',
            position: {
                corner: {
                    target: 'rightMiddle',
                    tooltip: 'leftTop',
                }
            },
            style: { 
                tip: true,
                name: 'blue',
                border: {
                    width: 2,
                    radius: 5,
                },
                width: { min: 200 },
                textAlign: 'justify',
            },
        });
    })
})

/*  Confirmation windows  */
$(document).ready(function() {
    $('.confirm-state').easyconfirm({
        locale: {
            title: voteit.translation['confirm-title'], 
            text: voteit.translation['confirm-state'], 
            button: [voteit.translation['no'], voteit.translation['yes']],
        }
    });
    $('.confirm-retract').easyconfirm({
        locale: {
            title: voteit.translation['confirm-title'], 
            text: voteit.translation['confirm-retract'], 
            button: [voteit.translation['no'], voteit.translation['yes']],
        }
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
voteit.minimize = {
    init: function(){
        $('.toggle_minimize').live('click', function() {
			min_parent = $(this).parents('.toggle_area');
			// Set parent class as opened or closed
			min_parent.toggleClass('toggle_opened').toggleClass('toggle_closed');
			
            var cookie_id = min_parent.attr('id');
            if (min_parent.hasClass('toggle_closed')) {
                $.cookie(cookie_id, 1);
            } else {
                $.cookie(cookie_id, null);
            }
        })
    }
}
$(document).ready(voteit.minimize.init);
