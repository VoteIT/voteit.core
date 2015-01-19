
def evolve(root):
    """ Evolve db to work with Arche instead. Removes anything that's a duplicate.
    """
    from repoze.catalog.catalog import Catalog
    from repoze.catalog.document import DocumentMap
    from arche.utils import find_all_db_objects

    #Create catalog - this will also clear the old catalog
    root.catalog = Catalog()
    root.document_map = DocumentMap()
    #FIXME: Add catalog indexes

    #Loop through all user objects
    _marker = object()
    for user in root.users.values:
        #Remove old password tokens
        delattr(user, '__token__')
        #Transfer password fields
        old_pw = user.field_storage['password'].get(_marker)
        if old_pw:
            user.__password_hash__ = old_pw
        del user.field_storage['password']

    for obj in find_all_db_objects(root):
        #Handle groups attribute and transfer to local role
        for (name, roles) in obj.__groups__.items():
            if name == 'role:Admin':
                name = 'role:Administrator'
            obj.local_roles[name] = roles
        delattr(obj, '__groups__')
