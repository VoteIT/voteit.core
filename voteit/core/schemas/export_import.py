import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.core import VoteITMF as _
from voteit.core.schemas.tmp_file_storage import MemoryTmpStore


IMPORT_NAME_REGEXP = r"[a-z\-0-9]{2,20}"


#Note: Don't use this instantiated version for anything else! They'll contain the same data! :)
tmpstore = MemoryTmpStore()


@schema_factory('ImportSchema')
class ImportSchema(colander.Schema):
    name = colander.SchemaNode(colander.String(),
                               title = _(u"Name, will be part of the url"),
                               description = _(u"Lowercase, numbers or hyphen is ok."),
                               validator = colander.Regex(IMPORT_NAME_REGEXP),)
    upload = colander.SchemaNode(
        deform.FileData(),
        widget=deform.widget.FileUploadWidget(tmpstore)
    )
