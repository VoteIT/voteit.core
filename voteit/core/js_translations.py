from voteit.core import VoteITMF as _ 
from voteit.core.models.interfaces import IJSUtil


def includeme(config):
    """ Add default js translations to system.
        Note that the msgids here are used by javascript - don't change them
        unless you know what you're doings!
    """
    util = config.registry.getUtility(IJSUtil)
    util.add_translations(
        yes = _(u"Yes"),
        no = _(u"No"),
        close = _(u"Close"),
        ok = _(u"Ok"),
        nothing_to_do = _(u"Nothing to do"),
        completed_successfully = _(u"Completed successfully"),
        there_was_an_error = _(u"There was an error during the operation. You may need to try again. Error was: "),
        confirm_title = _(u"Please confirm"),
        confirm_state = _(u"js_confirm_state",
                          default = u"Are you sure you want to change the state?"),
        confirm_retract = _(u"js_confirm_retract",
                            default = u"Are you sure you want to retract this proposal?"),
        user_info = _(u"About..."),
        more_tag_list = _(u"More..."),
        loading = _(u"Loading..."),
        poll = _(u"Poll"),
        answer_popup_title_answer = _("Reply"),
        answer_popup_title_comment = _("Comment"),
        voting_error_msg = _(u"js_voting_error_msg",
                             default = u"An error occurred while voting, please try again."),
        voting_timeout_msg = _(u"js_voting_timeout_msg",
                               default = u"Server didn't respond, many participants may be voteing right now, please try again."),
        waiting = _(u"Waiting..."),
        error_loading = _(u"js_error_loading",
                          default = u"There was an error loading data from server"),
        error_saving = _(u"js_error_saving",
                          default = u"There was an error saving data to the server"),
        close_message = _(u"Close message"),
        delete_poll_notification_title = _(u"Can not delete poll"),
        delete_poll_notification_text = _(u"delete_poll_notification_text",
                                          default=u"There are proposals in this poll that is in state voting, approved or denied. You need to manualy change the state of the proposals first."),
        permssions_updated_success = _(u"permssions_updated_success",
                                       default=u"Permssions was updated successfully"),
        permssions_updated_error = _(u"permssions_updated_error",
                                     default=u"There was an error updateing permissions"),
    )
