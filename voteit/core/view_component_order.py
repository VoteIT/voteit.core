#Default view component order

DEFAULT_VC_ORDER = (
    ('discussions', ('listing', 'add_form')),
    ('proposals', ('listing', 'add_form')),
    ('global_actions_anon', ('login', 'register')),
    ('global_actions_authenticated', ('user_profile', 'logout')),
    ('navigation_sections', ('closed', 'ongoing', 'upcoming', 'private')),
    ('meeting_actions', ('polls', 'moderator_menu', 'admin_menu', 'meetings', 'participants',)),
)
