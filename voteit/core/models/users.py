from repoze.folder import Folder


class Users(Folder):
    """ Container for all user objects """
    content_type = 'Users'
