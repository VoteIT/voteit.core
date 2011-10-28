/* Confirmation windows for workflow transactions
 * Currently needed by moderators on most pages, and by anyone with
 * permission to retract a proposal on the agenda item view.
 */
$(document).ready(function() {
    $('.confirm-state').easyconfirm({
        locale: {
            title: voteit.translation['confirm_title'], 
            text: voteit.translation['confirm_state'], 
            button: [voteit.translation['no'], voteit.translation['yes']],
        }
    });
    $('.confirm-retract').easyconfirm({
        locale: {
            title: voteit.translation['confirm_title'], 
            text: voteit.translation['confirm_retract'], 
            button: [voteit.translation['no'], voteit.translation['yes']],
        }
    });
});
