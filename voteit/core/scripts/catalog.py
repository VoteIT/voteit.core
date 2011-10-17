import transaction

from voteit.core.scripts.worker import ScriptWorker
from voteit.core.models.catalog import update_indexes, index_object
from voteit.core.models.interfaces import IBaseContent


def find_all_base_content(context):
    """ Traverser that will find all objects from context and below
        implementing IBaseContent, which is stings that the catalog care about.
    """
    def _recurse(base, results):
        for obj in base.values():
            if IBaseContent.providedBy(obj):
                results.add(obj)
            _recurse(obj, results)
    
    results = set()
    _recurse(context, results)
    return results


def update_catalog(*args):
    worker = ScriptWorker('update_catalog')
    
    cat = worker.root.catalog
    print "Clearing old data from catalog"
    cat.clear()
    
    updated_indexes = update_indexes(cat, reindex=False)
    if updated_indexes:
        print "The following indexes were added: %s" % ", ".join(updated_indexes)
    print "Performing reindex of catalog indexes and metadata. This might take some time."
    
    contents = find_all_base_content(worker.root)
    content_count = len(contents)
        
    #Note: There might be catalog aware models outside of this scope.
    #In that case, we need some way of finding them
    
    print "Found %s objects to update" % content_count
    
    i = 1
    p = 1
    for obj in contents:
        index_object(cat, obj)
        if p == 20:
            print "%s of %s done" % (i, content_count)
            p = 0
        i+=1
        p+=1
    
    print "Update complete - reindexed %s objects" % content_count
    print "Committing to database"
    transaction.commit()
    print "Done"
    
    worker.shutdown()
    