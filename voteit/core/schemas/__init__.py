

def includeme(config):
    config.include('.agenda_item')
    config.include('.agenda_template')
    config.include('.contact')
    config.include('.discussion_post')
    config.include('.invite_ticket')
    config.include('.meeting')
    config.include('.poll')
    config.include('.proposal')
    config.include('.site')
    config.include('.user')
    config.scan(__name__)
