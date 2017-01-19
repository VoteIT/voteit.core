

def evolve(root):
    from repoze.catalog.query import Any
    from repoze.catalog.query import Contains
    from repoze.catalog.query import Eq
    from pyramid.traversal import resource_path
    
    from voteit.core.models.catalog import reindex_object
    from voteit.core.models.catalog import resolve_catalog_docid
    print "Removing absolute urls in profile links"
    catalog = root.catalog
    
    host = None
    while not host:
        host = raw_input("Enter a host to replace (ex http://127.0.0.1:6543): ") 

    count, result = catalog.query(Eq('path', resource_path(root)) & \
                                  Contains('searchable_text', 'class="inlineinfo"') & \
                                  Any('content_type', ('DiscussionPost', 'Proposal', )))

    catalog = root.catalog
    print "Processing %s objects" % count
    for docid in result:
        # get object
        obj = resolve_catalog_docid(catalog, root, docid)
        obj.title = obj.title.replace(host, '')
        reindex_object(catalog, obj)
