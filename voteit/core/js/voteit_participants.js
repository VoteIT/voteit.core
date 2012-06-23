/* Mark all checkboxes in one column */
$(document).ready(function () {
    load_participants_data();
});

function load_participants_data() {

    $.getJSON('./_participants_data.json', function(data) {
        var uinfo_url = $("#js_config a[name=meeting_url]").attr('href') + '_userinfo?userid=';
        var userdata_rows = new Array();
        var data_tpl = $('#participant_data_template').clone();
        data_tpl.removeAttr('id');
        data_tpl.removeAttr('style');
        var yes_checkbox = $('#listing_templates .yes_icon').clone()
        var no_checkbox = $('#listing_templates .no_icon').clone()

        $('table.listing tbody').empty();
        for (var userid in data) {
            //Need to use hasOwnProperty?
            udata = data[userid];
            out = data_tpl.clone();
            console.log(udata);
            out.find('.userid').append('<a class="inlineinfo" href="' + uinfo_url + userid + '">' + userid + '</a>');
            out.find('.first_name').append(udata['first_name']);
            out.find('.last_name').append(udata['last_name']);
            out.find('.email').append('<a href="mailto:' + udata['email'] + '">' + udata['email'] + '</a>');
            out.find('.role').each(function() {
                var role = $(this).attr('name');
                var role_selector = "." + role.replace(':', '_');
                if ($.inArray(role, udata['roles']) != -1) {
                    out.find(role_selector).append(yes_checkbox.clone());
                }
                else {
                    out.find(role_selector).append(no_checkbox.clone());
                }

            })
            userdata_rows.push(out[0]);
        }
        $.each(userdata_rows, function(i, val) {
            if (i%2 == 0) {
                $(val).attr('class', 'odd');
            };
            $(val).appendTo('table.listing tbody');
        });
    });

};
