
def evolve(root):
    from arche.utils import get_content_factories
    if 'groups' not in root:
        factories = get_content_factories()
        root['groups'] = factories['Groups']()
