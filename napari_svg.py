from pluggy import HookimplMarker
from .utils import make_path_end_with_svg

napari_hook_implementation = HookimplMarker("napari")


@napari_hook_implementation
def napari_write_image(path, data, meta):
    """Write image data to an svg.

    Only two dimensional image data is supported (including rgb, and pyramid).
    For pyramid data the lowest resolution is used.

    Parameters
    ----------
    path : str
        Path to file, directory, or resource (like a URL).
    data : array or list of array
        Image data. Can be N dimensional. If the last dimension has length
        3 or 4 can be interpreted as RGB or RGBA if rgb is `True`. If a
        list and arrays are decreasing in shape then the data is from an image
        pyramid.
    meta : dict
        Image metadata.

    Returns
    -------
    bool : Return True if data is successfully written.
    """
    path = make_path_end_with_svg(path)

    # Check if data is a pyramid, and if so take only last layer
    if meta['is_pyramid']
        data = data[-1]

    # Check if more than 2 dimensional and if so error.
    if data.ndim - int(meta['is_rgb']) > 2:
        raise ValueError('Data must be 2 dimensional to save to svg')

    xml_list = image_to_xml_list(
        image,
        rgb=meta['rgb'],
        contrast_limits=meta['contrast_limits'],
        colormap=meta['colormap'],
        opacity=meta['opacity'],
    )    

    return True
