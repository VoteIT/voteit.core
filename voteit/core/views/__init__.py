
def includeme(config):
    config.include('.agenda_item')
    config.include('.cogwheel')
    config.scan(__name__)
