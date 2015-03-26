/* Main configuration */
if(typeof(voteit) == "undefined"){
    voteit = {};
}

/* Prioritize displaying flash messages in voteits area that floats under the menu */
arche.flash_slot_order = ['modal', 'voteit-main', 'main'];

voteit.unread_notify_timer = null;
voteit.unread_notify_interval = 6000;
voteit.unread_notify_url = null;
