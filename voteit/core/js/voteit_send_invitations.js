 $(document).ready(function() {

    var form = $('#send_invitations_form');
    var url = form.attr('action');
    var tickets_to_send = parseInt($('#tickets_to_send').text());

    function update_progress(remaining) {
        $('#tickets_to_send').text(remaining);
        var percentage_complete = Math.floor(100 - (remaining / tickets_to_send) * 100);
        $('#completed_percentage').text(percentage_complete);
        $('#completed_percentage_bar').width(String(percentage_complete) + '%');
    }

    function send_tickets() {
        var request = voteit.do_request(url, {data: form.serialize()});
        request.done(function(data) {
            update_progress(data['remaining']);
            if (data['remaining'] > 0) {
                setTimeout(send_tickets, 100);
            } else {
                flash_message(voteit.translation['completed_successfully']);
            }
        });
        request.fail(function(jqXHR) {
            setTimeout(send_tickets, 3000);
        });
    }
    
    send_tickets();
});