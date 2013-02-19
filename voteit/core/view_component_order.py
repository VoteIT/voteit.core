#Default view component order

DEFAULT_VC_ORDER = (
    ('discussions', ('listing', 'add_form')),
    ('proposals', ('listing', 'add_form')),
    ('global_actions_authenticated', ('logout',)),
    ('navigation_sections', ('navigation_section_header', 'ongoing', 'upcoming', 'closed', 'private')),
    ('meeting_actions', ('help_action', 'admin_menu', 'polls', 'settings_menu', 'meeting', 'participants_menu',)),
    ('moderator_actions_section', ('context_actions', 'workflow',)),
    ('context_actions', ('edit', 'delete', 'poll_config')),
    ('help_action', ('contact', 'wiki')),
    ('metadata_listing', ('user_tags', 'answer', 'retract', 'delete', 'tag', 'state','time')),
    ('agenda_item_top', ('description', 'tag_stats')),
    ('sidebar', ('login_pw', 'login_alt', 'navigation')), #latest_meeting_entries
)
