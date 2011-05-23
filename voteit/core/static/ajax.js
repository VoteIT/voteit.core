/* Menus */
$(document).ready(function () {
	$('#profile_toolbar ul li, #action_bar ul li').hover(
		function () {
			//show its submenu
			$('ul', this).slideDown(100);
		},
		function () {
			//hide its submenu
			$('ul', this).slideUp(100);
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
