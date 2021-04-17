import os
import numpy as np
from napari_plugin_engine import napari_hook_implementation
import warnings

from .xml_to_svg import xml_to_svg
from .layer_to_xml import (
    image_to_xml,
    points_to_xml,
    shapes_to_xml,
    vectors_to_xml,
)


labels_to_xml = image_to_xml
supported_layers = ['image', 'points', 'labels', 'shapes', 'vectors']


@napari_hook_implementation(trylast=True)
def napari_get_writer(path, layer_types):
    """Write layer data to an svg.

    Only two dimensional data is supported.

    Parameters
    ----------
    path : str
        Path to file, directory, or resource (like a URL).
    layer_types : list of str
        List of layer types that will be provided to the writer. Layer types
        must be contained in the list of currently supported layers.

    Returns
    -------
    callable
        function that accepts the path and a list of layer_data (where
        layer_data is ``(data, meta, layer_type)``) and writes each layer.
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
    """Write layer data to an svg.

    Parameters
    ----------
    path : str
        path to file/directory
    layer_data : list of napari.types.LayerData
        List of layer_data, where layer_data is ``(data, meta, layer_type)``.

    Returns
    -------
    path : str or None
        If data is successfully written, return the ``path`` that was written.
        Otherwise, if nothing was done, return ``None``.
    """    
    ext = os.path.splitext(path)[1]
    if ext == '':
        path = path + '.svg'
    elif ext != '.svg':
        # If an extension is provided then it must be `.svg`
        return None

    if len(layer_data) == 0:
        return None

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
            # get the extreema of all elements.
            with warnings.catch_warnings():
                # Taking the nanmin and nanmax of an axis of all nan
                # raises a warning and returns nan for that axis
                # as we have do an explict nan_to_num in xml_to_svg this
                # behaviour is acceptable and we can filter the
                # warning, see https://github.com/napari/napari-svg/pull/12
                warnings.filterwarnings(
                    'ignore', message='All-NaN axis encountered'
                )
                full_extrema = np.array([
                                    np.nanmin([full_extrema[0], extrema[0]], axis=0),
                                    np.nanmax([full_extrema[1], extrema[1]], axis=0),
                                ])

    # Generate svg string
    svg = xml_to_svg(full_xml_list, extrema=full_extrema)

    # Write svg string
    with open(path, 'w') as file:
        file.write(svg)

    return path


@napari_hook_implementation(trylast=True)
def napari_write_image(path, data, meta):
    """Write image data to an svg.

    Only two dimensional image data is supported (including rgb, and multiscale).
    For multiscale data the lowest resolution is used.

    Parameters
    ----------
    path : str
        Path to file, directory, or resource (like a URL).
    data : array or list of array
        Image data. Only two dimensional data (including rgb, and multiscale)
        is supported. For multiscale data the lowest resolution is used.
    meta : dict
        Image metadata.

    Returns
    -------
    path : str or None
        If data is successfully written, return the ``path`` that was written.
        Otherwise, if nothing was done, return ``None``.
    """
    ext = os.path.splitext(path)[1]
    if ext == '':
        path = path + '.svg'
    elif ext != '.svg':
        # If an extension is provided then it must be `.svg`
        return None

    # Generate xml list and data extrema
    xml_list, extrema = image_to_xml(data, meta)
    
    # Generate svg string
    svg = xml_to_svg(xml_list, extrema=extrema)
    
    # Write svg string
    with open(path, 'w') as file:
        file.write(svg)

    return path



@napari_hook_implementation(trylast=True)
def napari_write_labels(path, data, meta):
    """Write labels data to an svg.

    Only two dimensional labels data is supported (including multiscale).
    For multiscale data the lowest resolution is used.

    Parameters
    ----------
    path : str
        Path to file, directory, or resource (like a URL).
    data : array or list of array
        Labels data. Only two dimensional data (including multiscale) is supported.
        For multiscale data the lowest resolution is used.
    meta : dict
        Labels metadata.

    Returns
    -------
    path : str or None
        If data is successfully written, return the ``path`` that was written.
        Otherwise, if nothing was done, return ``None``.
    """
    ext = os.path.splitext(path)[1]
    if ext == '':
        path = path + '.svg'
    elif ext != '.svg':
        # If an extension is provided then it must be `.svg`
        return None

    # Generate xml list and data extrema
    xml_list, extrema = labels_to_xml(data, meta)
    
    # Generate svg string
    svg = xml_to_svg(xml_list, extrema=extrema)
    
    # Write svg string
    with open(path, 'w') as file:
        file.write(svg)

    return path


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
        Points data. Only two dimensional data is supported.
    meta : dict
        Points metadata.

    Returns
    -------
    path : str or None
        If data is successfully written, return the ``path`` that was written.
        Otherwise, if nothing was done, return ``None``.
    """
    ext = os.path.splitext(path)[1]
    if ext == '':
        path = path + '.svg'
    elif ext != '.svg':
        # If an extension is provided then it must be `.svg`
        return None

    # Generate xml list and data extrema
    xml_list, extrema = points_to_xml(data, meta)
    
    # Generate svg string
    svg = xml_to_svg(xml_list, extrema=extrema)
    
    # Write svg string
    with open(path, 'w') as file:
        file.write(svg)

    return path


@napari_hook_implementation
def napari_write_shapes(path, data, meta):
    """Write shapes data to an svg.

    Only two dimensional shapes data is supported. Z ordering of the shapes
    will be taken into account.

    Parameters
    ----------
    path : str
        Path to file, directory, or resource (like a URL).
    data : list of array
        Shapes data. Only two dimensional data is supported.
    meta : dict
        Shapes metadata.

    Returns
    -------
    path : str or None
        If data is successfully written, return the ``path`` that was written.
        Otherwise, if nothing was done, return ``None``.
    """
    ext = os.path.splitext(path)[1]
    if ext == '':
        path = path + '.svg'
    elif ext != '.svg':
        # If an extension is provided then it must be `.svg`
        return None

    # Generate xml list and data extrema
    xml_list, extrema = shapes_to_xml(data, meta)
    
    # Generate svg string
    svg = xml_to_svg(xml_list, extrema=extrema)
    
    # Write svg string
    with open(path, 'w') as file:
        file.write(svg)

    return path


@napari_hook_implementation
def napari_write_vectors(path, data, meta):
    """Write vectors data to an svg.

    Only two dimensional vectors data is supported. Each vector is represented
    by a line.

    Parameters
    ----------
    path : str
        Path to file, directory, or resource (like a URL).
    data : array
        Vectors data. Only two dimensional data is supported.
    meta : dict
        Vectors metadata.

    Returns
    -------
    path : str or None
        If data is successfully written, return the ``path`` that was written.
        Otherwise, if nothing was done, return ``None``.
    """
    ext = os.path.splitext(path)[1]
    if ext == '':
        path = path + '.svg'
    elif ext != '.svg':
        # If an extension is provided then it must be `.svg`
        return None

    # Generate xml list and data extrema
    xml_list, extrema = vectors_to_xml(data, meta)
    
    # Generate svg string
    svg = xml_to_svg(xml_list, extrema=extrema)
    
    # Write svg string
    with open(path, 'w') as file:
        file.write(svg)

    return path
