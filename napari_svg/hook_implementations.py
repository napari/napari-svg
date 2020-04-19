import os
import numpy as np
from pluggy import HookimplMarker
from .xml_conversion import xml_to_svg, image_to_xml, points_to_xml


napari_hook_implementation = HookimplMarker("napari")
supported_layers = ['image', 'points']


@napari_hook_implementation
def napari_get_writer(path, layer_types):
    """Write layer data to an svg.

    Only two dimensional data is supported.

    Parameters
    ----------
    path : str
        Path to file, directory, or resource (like a URL).
    layer_types : list of str
        List of layer types that will be provided to the writer. Only 'image'
        and 'points' layers are currently supported.
    meta : dict
        Image metadata.

    Returns
    -------
    bool : Return True if data is successfully written.
    """
    # Check that only supported layers have been passed
    for lt in set(layer_types):
        if lt not in supported_layers:
            return None

    ext = os.path.splitext(path)[1]
    if ext == '':
        path = path + '.svg'
    elif ext != '.svg':
        # If an extension is provided then it must be `.svg`
        return None

    return writer


def writer(path, layer_data):
    """Write data to an svg.
    """
    if len(layer_data) == 0:
        return True
    
    ext = os.path.splitext(path)[1]
    if ext == '':
        path = path + '.svg'
    elif ext != '.svg':
        # If an extension is provided then it must be `.svg`
        return False

    # Generate xml list and data extrema for all layers
    full_xml_list = []
    full_extrema = None
    for ld in layer_data:
        function_string = ld[2] + '_to_xml(ld[0], ld[1])'
        xml_list, extrema = eval(function_string)
        full_xml_list += xml_list
        if full_extrema is None:
            full_extrema = extrema
        else:
            full_extrema = np.array([
                                np.min([full_extrema[0], extrema[0]], axis=0),
                                np.max([full_extrema[1], extrema[1]], axis=0),
                            ])

    # Generate svg string
    svg = xml_to_svg(full_xml_list, extrema=full_extrema)

    # Write svg string
    with open(path, 'w') as file:
        file.write(svg)

    return True


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
        Image data. Only two dimensional data (including rgb, and pyramid).
        For pyramid data the lowest resolution is used.
    meta : dict
        Image metadata.

    Returns
    -------
    bool : Return True if data is successfully written.
    """
    ext = os.path.splitext(path)[1]
    if ext == '':
        path = path + '.svg'
    elif ext != '.svg':
        # If an extension is provided then it must be `.svg`
        return False

    # Generate xml list and data extrema
    xml_list, extrema = image_to_xml(data, meta)
    
    # Generate svg string
    svg = xml_to_svg(xml_list, extrema=extrema)
    
    # Write svg string
    with open(path, 'w') as file:
        file.write(svg)

    return True


@napari_hook_implementation
def napari_write_points(path, data, meta):
    """Write points data to an svg.

    Only two dimensional points data is supported. Z ordering of the points
    will be taken into account. Each point is represented by a circle. Support
    for other symbols is not yet implemented.

    Parameters
    ----------
    path : str
        Path to file, directory, or resource (like a URL).
    data : array
        Points data. Only two dimensional data.
    meta : dict
        Points metadata.

    Returns
    -------
    bool : Return True if data is successfully written.
    """
    ext = os.path.splitext(path)[1]
    if ext == '':
        path = path + '.svg'
    elif ext != '.svg':
        # If an extension is provided then it must be `.svg`
        return False

    # Generate xml list and data extrema
    xml_list, extrema = points_to_xml(data, meta)
    
    # Generate svg string
    svg = xml_to_svg(xml_list, extrema=extrema)
    
    # Write svg string
    with open(path, 'w') as file:
        file.write(svg)

    return True
