/* Menus
 * example layout:
 * <div class="dropdown_menu">
 *   <a class="menu_header">x</a>
 *   <div class="menu_body">Dropdown menu here</a>
 * </div>
 */
$(document).ready(function () {
	$('.dropdown_menu').hover(
		function () {
			//show its submenu
			$('.menu_body', this).slideDown(100);
		},
		function () {
			//hide its submenu
			$('.menu_body', this).slideUp(100);
		}
	);
});

/*  */
$(document).ready(function() {
    $(".expression_form").live('submit', function(event) {
        /* stop form from submitting normally */
        event.preventDefault(); 
            
        /* get some values from elements on the page: */
        var $form = $( this ),
            tag = $form.find('input[name="tag"]').val(),
            _do = $form.find('input[name="do"]').val(),
            display_name = $form.find('input[name="display_name"]').val(),
            url = $form.attr('action'),
            id = $form.attr('id');

        /* Send the data using post and put the results in a div */
        $.post(url, {'tag': tag, 'do': _do, 'display_name': display_name},
          function(data) {
              $("#"+id).html(data);
          }
        );
    });
});
