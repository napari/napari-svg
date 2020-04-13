import os


def make_path_end_with_svg(path):
    """Make path end with an svg extension.

    Parameters
    ----------
    path : str
        Path that should end with an svg extension
    """
    ext = os.path.splitext(path)[1]
    if ext != '.svg':
        path = path + '.svg'
    return path
