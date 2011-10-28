/* VoteIT deform fixes */
/* Show description */
$(document).ready(function() {
    $('label.desc').each(function() {
        var desc = $(this).attr('title');
        if(desc != '')
            $(this).after('<p>'+desc+'</p>');
    });
});
