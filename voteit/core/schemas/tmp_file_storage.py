
class MemoryTmpStore(dict):
    """ Instances of this class implement the
        deform.interfaces.FileUploadTempStore interface.
        It will be shared across threads, so don't use it for anything
        important.
        It's usable as a buffer for uploaded files while validation occurs.
    """
    def preview_url(self, uid):
        return None

