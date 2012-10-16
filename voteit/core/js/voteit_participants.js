$(document).ready(function () {
    voteit.participants_tpl = {};
    voteit.participants_tpl['data_tpl'] = $('#participant_data_template').clone();
    voteit.participants_tpl['data_tpl'].removeAttr('id');
    voteit.participants_tpl['data_tpl'].removeAttr('style');
    voteit.participants_tpl['yes_icon'] = $('#listing_templates .yes_icon').clone()
    voteit.participants_tpl['no_icon'] = $('#listing_templates .no_icon').clone()
    voteit.participants_tpl['userid_tpl'] = $('#listing_templates .userid').clone()
    voteit.participants_tpl['listing_checkbox'] = $('#listing_templates .listing_checkbox').clone()
    load_participants_data();
});

function get_part_tpl(name) {
    return voteit.participants_tpl[name].clone();
}

function load_participants_data() {
    var userdata_rows = new Array();

    $.getJSON('./_participants_data.json', function(data) {

        $('table.listing tbody').empty();
        $('#permissions thead span.count').each(function() {
			$(this).text(0);
        });
        for (var userid in data) {
            //Need to use hasOwnProperty?
            udata = data[userid];
            out = get_part_tpl('data_tpl');
            //console.log(udata);
            var userid_data = get_part_tpl('userid_tpl');
            userid_data.find('input').attr('value', userid);
            var userid_atag = userid_data.find('a');
            userid_atag.attr('href', userid_atag.attr('href') + userid);
            userid_atag.append(userid);
            out.find('.userid').append(userid_data);
            out.find('.first_name').append(udata['first_name']);
            out.find('.last_name').append(udata['last_name']);
            out.find('.email').append('<a href="mailto:' + udata['email'] + '">' + udata['email'] + '</a>');
            for(var extra in udata['extras']) {
            	out.find('.'+extra).append(udata['extras'][extra]);
            }
            out.find('.role').each(function() {
                var role = $(this).attr('name');
                var role_selector = "." + role.replace(':', '_');
                var listing_checkbox = get_part_tpl('listing_checkbox');
                $(listing_checkbox).attr('value', role);
                if ($.inArray(role, udata['roles']) != -1) {
                    out.find(role_selector).append(get_part_tpl('yes_icon'));
                    $(listing_checkbox).attr('checked', true);
                    // update role count in header 
                    var count_span = $('#permissions thead span.count'+role_selector);
                    var count = parseInt(count_span.text());
                    if(isNaN(count))
                    	count_span.text(1);
                	else
                		count_span.text(++count);
                }
                else {
                    out.find(role_selector).append(get_part_tpl('no_icon'));
                }
                if ($(this).hasClass('read_only') == false) {
                    out.find(role_selector).append(listing_checkbox);
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
