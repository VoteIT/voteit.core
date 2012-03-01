#Default view component order

DEFAULT_VC_ORDER = (
    ('discussions', ('listing', 'add_form')),
    ('proposals', ('listing', 'add_form')),
    ('global_actions_anon', ('login', 'register')),
    ('global_actions_authenticated', ('user_profile', 'logout')),
    ('navigation_sections', ('closed', 'ongoing', 'upcoming', 'private')),
    ('meeting_actions', ('admin_menu', 'polls', 'settings_menu', 'meeting', 'participants_menu',)),
    ('moderator_actions_section', ('context_actions', 'workflow',)),
    ('context_actions', ('edit', 'delete', 'poll_config')),
    ('help_action', ('contact', 'wiki')),
)
