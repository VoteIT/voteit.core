def includeme(config):
    config.scan(__name__)
    config.include('.auto_claim_ticket')
