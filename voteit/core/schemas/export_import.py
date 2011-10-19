import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.core import VoteITMF as _
from voteit.core.schemas.tmp_file_storage import tmpstore

#FIXME: Validate name

@schema_factory('ImportSchema')
class ImportSchema(colander.Schema):
    name = colander.SchemaNode(colander.String(),)
    upload = colander.SchemaNode(
        deform.FileData(),
        widget=deform.widget.FileUploadWidget(tmpstore)
    )