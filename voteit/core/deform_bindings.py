from deform import Form


def append_search_path(path):
    """ Add a search path to deform. This is the way to register
        custom widget templates.
    """
    current = list(Form.default_renderer.loader.search_path)
    current.append(path)
    Form.default_renderer.loader.search_path = tuple(current)
