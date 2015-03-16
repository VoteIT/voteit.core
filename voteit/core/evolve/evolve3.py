

def evolve(root):
    import re
    
    from pyramid.traversal import resource_path
    from repoze.catalog.query import Any
    from repoze.catalog.query import Contains
    from repoze.catalog.query import Eq
    
    from voteit.core.models.catalog import resolve_catalog_docid
    from voteit.core.models.catalog import index_object
    from voteit.core.models.catalog import unindex_object
    from voteit.core.models.catalog import update_indexes
    from voteit.core.models.unread import Unread
    from voteit.core.models.user_tags import UserTags
    from voteit.core.security import ROLE_OWNER
    from voteit.core.scripts.catalog import find_all_base_content

    print "initial reindex of catalog to make sure everything is up to date"
    clear_and_reindex(root)

    print "changing user profiles to lowercase"
    # loop through profiles
    # list of possible duplicate errors
    errors = []
    lowercased = []
    # loop all users and build a list of old and new userids
    users = root.users
    userids = []
    existing_userids = set()

    for userid in users:
        # get profile
        profile = users[userid]
        # if they are uppercase convert
        if userid != userid.lower():
            print "%s %s" % (userid, profile.get_field_value('email', ''))
            # new userid
            userid_lower = userid.lower()
            # check so there is no profile with the same lowercase userid if so throw exception
            altered = False
            while userid_lower in users or userid_lower in existing_userids:
                print "already a userid named %s in users or was picked already" % userid_lower
                userid_lower = raw_input("Enter a new userid: ")
                altered = True
            if altered:
                # add to errror list
                errors.append([userid, userid_lower, profile.get_field_value('email', '')])
            else:
                lowercased.append([userid, userid_lower, profile.get_field_value('email', '')])
            userids.append((userid, userid_lower))
        existing_userids.add(userid.lower())
            
    # loop userids that is going to change
    for (userid, userid_lower) in userids:
        change_votes(root, userid, userid_lower)
        change_unread(root, userid, userid_lower)
        change_usertags(root, userid, userid_lower)
        change_mentions(root, userid, userid_lower)
        # change groups on root
        change_groups(root, userid, userid_lower)
        # change groups on meetings
        for meeting in root.get_content(content_type='Meeting'):
           change_groups(meeting, userid, userid_lower)
        change_creator_and_owner(root, userid, userid_lower)
        # will not change rss, logs
        # get profile
        profile = users[userid]
        # remove profile from storage
        del users[userid]
        # Reindex and remove index not a problem as long as we clear the index afterwards
        # add profile with new userid
        users[userid_lower] = profile
    
    clear_and_reindex(root)

    # check that timestamps doesn't change
    # print list of duplicate errors with olduserid new userid and email
    print "\n"
    print "The following userids were lowercased, displayed as 'from;to;email':"
    for info in lowercased:
        print "%s;%s;%s" % tuple(info)
    print "\n-------------------\n"
    print "The following have changed userid:"
    for error in errors:
        print "%s;%s;%s" % tuple(error)
    print "\n"

def clear_and_reindex(root):
    # reindex catalog
    root.catalog.clear()
    updated_indexes = update_indexes(root.catalog, reindex=False)
    contents = find_all_base_content(root)
    content_count = len(contents)

    #Note: There might be catalog aware models outside of this scope.
    #In that case, we need some way of finding them
    print "Found %s objects to update" % content_count
    i = 1
    p = 1
    for obj in contents:
        index_object(root.catalog, obj)
        if p == 100:
            print "%s of %s done" % (i, content_count)
            p = 0
        i+=1
        p+=1


def change_creator_and_owner(root, userid, userid_lower):
    catalog = root.catalog
    
    result = catalog.search(path=resource_path(root), creators=(userid,))[1]
    
    for docid in result:
        # get object
        obj = resolve_catalog_docid(catalog, root, docid)
        
        # change creators
        creators = list(obj.creators) # get creators
        creators.remove(userid) # remove old userid
        creators.append(userid_lower) # add new userid
        obj.creators = creators # set creators
        
        # change owner if userid is owner
        if ROLE_OWNER in obj.get_groups(userid):
            obj.del_groups(userid, (ROLE_OWNER, ), event=False) # remove old userid
            obj.add_groups(userid_lower, (ROLE_OWNER, ), event=False) # add new userid
            

def change_groups(obj, userid, userid_lower):
    groups = obj.get_groups(userid)
    for group in groups:
        obj.del_groups(userid, (group, ), event=False) # remove old userid
        obj.add_groups(userid_lower, (group, ), event=False) # add new userid

def change_votes(root, userid, userid_lower):
    catalog = root.catalog
    result = catalog.search(content_type='Vote', creators=(userid,))[1]
    for docid in result:
        # get vote
        obj = resolve_catalog_docid(catalog, root, docid)
        # get parent of vote 
        parent = obj.__parent__
        # if userid is in parent container and the object in the parent is the object from the catalog
        if userid in parent and parent[userid] == obj:
            #Remember that this part won't reindex the catalog as it normally does.
            unindex_object(catalog, parent[userid])
            del parent[userid] # remove with old userid
            parent[userid_lower] = obj # add with new userid
            index_object(catalog, obj)

def change_unread(root, userid, userid_lower):
    catalog = root.catalog
    result = catalog.search(path=resource_path(root), unread=(userid,))[1]
    for docid in result:
        # get object
        obj = resolve_catalog_docid(catalog, root, docid)
        # get unread adapter
        unread = Unread(obj)
        
        if userid in unread.unread_storage:
            unread.unread_storage.remove(userid) # remove old userid
            unread.unread_storage.add(userid_lower) # add new userid

def change_usertags(root, userid, userid_lower):
    catalog = root.catalog
    result = catalog.search(path=resource_path(root), like_userids=(userid,))[1]
    for docid in result:        
        obj = resolve_catalog_docid(catalog, root, docid)
        # get unread adapter
        usertags = UserTags(obj)
        for tag in usertags.tags_storage:
            if userid in usertags.tags_storage[tag]:
                usertags.tags_storage[tag].remove(userid) # remove old userid
                usertags.tags_storage[tag].add(userid_lower) # add new userid
            
def change_mentions(root, userid, userid_lower):
    catalog = root.catalog
    result = catalog.query(Eq('path', resource_path(root)) & \
                           Contains('searchable_text', userid) & \
                           Any('content_type', ('DiscussionPost', 'Proposal', )))[1]
    for docid in result:
        # get object
        obj = resolve_catalog_docid(catalog, root, docid)
        title = obj.title
        for match in re.finditer('<a class="inlineinfo" href="http:\/\/[\da-z.-:]*/[\w-]*/_userinfo\?userid=('+userid+')" title="[\w\s-]*">@('+userid+')</a>', title, re.UNICODE):
            title = title[0:match.start(1)] + userid_lower + title[match.end(1):len(title)] # replace in url
            title = title[0:match.start(2)] + userid_lower + title[match.end(2):len(title)] # replace in text
        obj.title = title
