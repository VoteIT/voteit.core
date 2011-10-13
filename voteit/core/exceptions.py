

class TokenValidationError(Exception):
    """ A security token didn't match input value, or was never set. """
