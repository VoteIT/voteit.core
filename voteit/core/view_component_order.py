#Default view component order

DEFAULT_VC_ORDER = (
    ('discussions', ('listing', 'add_form')),
    ('proposals', ('listing', 'add_form')),
    ('global_actions_anon', ('login', 'register')),
    ('global_actions_authenticated', ('user_profile', 'logout')),
    ('navigation_sections', ('latest_meeting_entries', 'meeting_sections_header', 'ongoing', 'upcoming', 'closed', 'private')),
    ('meeting_actions', ('search', 'help_action', 'admin_menu', 'polls', 'settings_menu', 'meeting', 'participants_menu',)),
    ('moderator_actions_section', ('context_actions', 'workflow',)),
    ('context_actions', ('edit', 'delete', 'poll_config')),
    ('help_action', ('contact', 'wiki')),
    ('metadata_listing', ('state','time','retract', 'user_tags','answer','tag')),
)
