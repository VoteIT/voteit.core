
def evolve(root):
    """ Evolve db to work with Arche instead. Removes anything that's a duplicate.
    """
    from arche.utils import find_all_db_objects
    try:
        import betahaus.pyracont #test
    except ImportError:
        print "IMPORTANT! password fields needed to make this migration. Install betahaus.pyracont"
        raise
    #Loop through all user objects
    _marker = object()
    for user in root.users.values():
        #Remove old password tokens
        if hasattr(user, '__token__'):
            delattr(user, '__token__')
        #Transfer password fields
        old_pw = user.field_storage.get('password', {}).get(_marker)
        if old_pw:
            user.__password_hash__ = old_pw
        user.field_storage.pop('password', None)

    for obj in find_all_db_objects(root):
        #Handle groups attribute and transfer to local role
        if hasattr(obj, '__groups__'):
            for (name, roles) in obj.__groups__.items():
                new_roles = set(roles)
                if 'role:Admin' in new_roles:
                    new_roles.remove('role:Admin')
                    new_roles.add('role:Administrator')
                obj.local_roles[name] = new_roles
            delattr(obj, '__groups__')
