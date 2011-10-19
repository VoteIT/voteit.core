from zope.interface import implements
from zope.component import adapts
from cStringIO import StringIO
from pyramid.response import Response

from voteit.core.models.interfaces import IExportImport
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.scripts.catalog import find_all_base_content
from voteit.core.models.catalog import index_object


class ExportImport(object):
    __doc__ = IExportImport.__doc__
    implements(IExportImport)
    adapts(ISiteRoot)
    
    def __init__(self, context):
        self.context = context

    def _export_buffer(self, obj):
        f = StringIO()
        obj._p_jar.exportFile(obj._p_oid, f)
        return f

    def download_export(self, obj):
        export = self._export_buffer(obj).getvalue()
        return Response(content_type = 'application/data',
                        content_disposition = 'inline; filename=hello_world.exp',
                        body = export)

    def import_data(self, parent, name, filedata):
        connection = parent._p_jar
        new_obj = connection.importFile(filedata['fp'])
        if ISiteRoot.providedBy(new_obj):
            raise ValueError("Importing a new site root is not supported. If you want to import a complete database, simply copy the database file Data.fs")
        parent[name] = new_obj
        #Reindex all objects
        for obj in find_all_base_content(new_obj):
            index_object(self.context.catalog, obj)


def includeme(config):
    """ Include ExportImport adapter. This will make the views associated with this usable. """
    config.registry.registerAdapter(ExportImport, (ISiteRoot,), IExportImport)
