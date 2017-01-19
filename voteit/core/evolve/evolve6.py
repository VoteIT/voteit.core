
def evolve(root):
    from pyramid.threadlocal import get_current_registry
    from pyramid.traversal import find_interface
    
    from voteit.core.models.catalog import resolve_catalog_docid
    from voteit.core.models.catalog import index_object
    from voteit.core.models.catalog import update_indexes
    from voteit.core.models.interfaces import IMeeting
    from voteit.core.models.interfaces import IProposalIds
    from voteit.core.scripts.catalog import find_all_base_content

    print "initial reindex of catalog to make sure everything is up to date"
    clear_and_reindex(root)
    
    registry = get_current_registry()

    print "extracting the last aid from poroposals"
    catalog = root.catalog
    result = catalog.search(content_type="Proposal")[1]
    for docid in result:
        print "--------------------------------------------------"
        proposal = resolve_catalog_docid(catalog, root, docid)
        meeting = find_interface(proposal, IMeeting)
        proposal_ids = registry.queryAdapter(meeting, IProposalIds)
        
        print "extracting from proposal %s" % proposal.__name__
        
        # get aid from propsoal
        aid_int = proposal.get_field_value('aid_int')
        print "proposal aid %s" % aid_int
        
        # get the aid for the creator currently saved in  the meeting
        creators = proposal.get_field_value('creators')
        current_aid = proposal_ids.get(creators[0])
        print "current aid for creator %s" % current_aid

        # if current aid is empty or the aid from the proposal is 
        # greater then the current one, save it in the meeting 
        if not current_aid or aid_int > current_aid:
            proposal_ids.add(creators[0], aid_int)
    
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