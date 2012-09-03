import re

from pyramid.traversal import resource_path
from pyramid.traversal import find_interface
from repoze.catalog.query import Eq

from voteit.core.models.catalog import resolve_catalog_docid
from voteit.core.models.catalog import index_object
from voteit.core.models.catalog import reindex_object
from voteit.core.models.catalog import update_indexes
from voteit.core.models.interfaces import IMeeting
from voteit.core.scripts.catalog import find_all_base_content


def evolve(root):

    print "initial reindex of catalog to make sure everything is up to date"
    clear_and_reindex(root)

    print "adding aid to poroposals"
    catalog = root.catalog
    result = catalog.search(content_type="Proposal")[1]
    for docid in result:
        obj = resolve_catalog_docid(catalog, root, docid)
        print obj
        meeting = find_interface(obj, IMeeting)
        creators = obj.get_field_value('creators')
        if creators:
            creator = creators[0]
            for n in range(1, 500):
                aid = "%s-%s" % (creator, n)
                
                #check that aid is unique in meeting
                count, result = catalog.query(Eq('path', resource_path(meeting)) & \
                                              Eq('aid', aid))
                if count == 0:
                    obj.set_field_value('aid', aid)
                    reindex_object(root.catalog, obj, indexes=('aid',))
                    continue
    
    print "initial reindex of catalog to make sure everything is up to date"
    clear_and_reindex(root)
    
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