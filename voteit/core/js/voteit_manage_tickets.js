$(document).ready(function() {
    $("table.listing").tablesorter({headers: { 0: { sorter: false}}});
    $('input[name="select_all"]').change(function(event) {
        var setval = $(this).prop('checked');
        console.log(setval);
        $('#tickets_table tbody td input[type="checkbox"]:visible').prop('checked', setval);
        console.log($('#tickets_table tbody td input[type="checkbox"]').length);
        count_selected();
    });
    $('#search_email').bind('keypress keydown keyup', function(e) {
       if(e.keyCode == 13) {
           e.preventDefault(); 
           $(this).change();
       }
    });
    $('#search_email').change(function(event) {
        var search = $(this).val();
        //Show all
        if (search == '') {
            $('#tickets_table tbody tr').show();
            $('.selection_email').text('');
        }
        //Search active
        else {
            $('#tickets_table tbody tr').hide();
            var matching = $('#tickets_table tbody td.email:contains("' + search +'")');
            matching.parent().show();
            $('.selection_email').text('(' + matching.length + ')');
        }
    });
    $('#tickets_table tbody td input[type="checkbox"]').on('click', function(event) {
        count_selected();
    });
    function count_selected() {
        //What to with invisible?
        var selected_count = $('#tickets_table tbody td input[type="checkbox"]:checked').length;
        $('#selected_count').text(selected_count);
    };
});
