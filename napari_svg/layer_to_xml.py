from xml.etree.ElementTree import Element
from base64 import b64encode
import numpy as np
from copy import copy
from imageio import imwrite
from vispy.color import get_colormap
from ._shape_to_xml import (
    ellipse_to_xml,
    line_to_xml,
    path_to_xml,
    polygon_to_xml,
    rectangle_to_xml,
)


shape_type_to_xml = {
    'ellipse': ellipse_to_xml,
    'line': line_to_xml,
    'path': path_to_xml,
    'polygon': polygon_to_xml,
    'rectangle': rectangle_to_xml,
}


def image_to_xml(data, meta):
    """Generates a xml data for an image.

    Only two dimensional data (including rgb, and multiscale) is supported. For
    multiscale data the lowest resolution is used.

    The xml data is a list with a single xml element that defines the
    currently viewed image as a png according to the svg specification.

    Parameters
    ----------
    data : array or list of array
        Image data. Only two dimensional data (including rgb, and multiscale) is
        supported. For multiscale data the lowest resolution is used.
    meta : dict
        Image metadata.

    Returns
    -------
    xml_list : list of xml.etree.ElementTree.Element
        List of a single xml element specifying the image as a png according to
        the svg specification.
    extrema : array (2, 2)
        Extrema of data, specified as a minumum then maximum of the (x, y)
        coordinates.
    """
    # Extract metadata parameters
    if 'multiscale' in meta:
        multiscale = meta['multiscale']
    else:
        multiscale = False

    if 'rgb' in meta:
        rgb = meta['rgb']
    else:
        rgb = False

    if 'contrast_limits' in meta:
        contrast_limits = meta['contrast_limits']
    else:
        contrast_limits = [0, 1]

    if 'colormap' in meta:
        colormap_name = meta['colormap']

        # convert 'gray' colormap name to 'grays' for vispy compatibility
        # see: https://github.com/napari/napari-svg/pull/12
        if colormap_name == 'gray':
            colormap_name = 'grays'
    else:
        colormap_name = 'grays'

    if 'opacity' in meta:
        opacity = meta['opacity']
    else:
        opacity = 1

    # Check if data is multiscale, and if so take only last layer
    if multiscale:
        data = data[-1]

    # Check if more than 2 dimensional and if so error.
    if data.ndim - int(rgb) > 2:
        raise ValueError('Image must be 2 dimensional to save as svg')
    else:
        image = data

    # Find extrema of data
    extrema = np.array([[0, 0], [image.shape[0], image.shape[1]]])

    if rgb:
        mapped_image = image
    else:
        # apply contrast_limits to data
        image = np.clip(
            image, contrast_limits[0], contrast_limits[1]
        )
        image = image - contrast_limits[0]
        color_range = contrast_limits[1] - contrast_limits[0]
        if color_range != 0:
            image = image / color_range

        # get colormap
        # TODO: Currently we only support vispy colormaps, need to
        # add support for all napari colormaps, matters for Labels too.
        cmap = get_colormap(colormap_name)
            
        # apply colormap to data
        mapped_image = cmap[image.ravel()]
        mapped_image = mapped_image.RGBA.reshape(image.shape + (4,))

    image_str = imwrite('<bytes>', mapped_image, format='png')
    image_str = "data:image/png;base64," + str(b64encode(image_str))[2:-1]
    props = {'xlink:href': image_str}

    width = str(image.shape[1])
    height = str(image.shape[0])

    xml = Element(
        'image', width=width, height=height, opacity=str(opacity), **props
    )
    xml_list = [xml]
    
    return xml_list, extrema


def points_to_xml(data, meta):
    """Generates a xml data for points.

    Only two dimensional points data is supported. Z ordering of the points
    will be taken into account. Each point is represented by a circle. Support
    for other symbols is not yet implemented.

    Parameters
    ----------
    data : array
        Points data. Only two dimensional points data is supported.
    meta : dict
        Points metadata.

    Returns
    -------
    xml_list : list of xml.etree.ElementTree.Element
        List of xml elements defining each point according to the
        svg specification
    extrema : array (2, 2)
        Extrema of data, specified as a minumum then maximum of the (x, y)
        coordinates.
    """
    # Extract metadata parameters
    if 'size' in meta:
        size = np.mean(meta['size'], axis=1)
    else:
        size = np.ones(data.shape[0])

    if 'face_color' in meta:
        face_color = meta['face_color']
    else:
        face_color = np.ones((data.shape[0], 4))

    if 'edge_color' in meta:
        edge_color = meta['edge_color']
    else:
        edge_color = np.zeros((data.shape[0], 4))
        edge_color[:, 3] = 1

    if 'edge_width' in meta:
        edge_width = meta['edge_width']
    else:
        edge_width = 1

    if 'opacity' in meta:
        opacity = meta['opacity']
    else:
        opacity = 1

    # Check if more than 2 dimensional and if so error.
    if data.shape[1] > 2:
        raise ValueError('Points must be 2 dimensional to save as svg')
    else:
        points = data

    # Find extrema of data
    extrema = np.array([points.min(axis=0), points.max(axis=0)])

    props = {'stroke-width': str(edge_width), 'opacity': str(opacity)}

    xml_list = []
    for p, s, fc, ec in zip(points, size, face_color, edge_color):
        cx = str(p[1])
        cy = str(p[0])
        r = str(s / 2)
        fc_int = (255 * fc).astype(int)
        fill = f'rgb{tuple(fc_int[:3])}'
        ec_int = (255 * ec).astype(int)
        stroke = f'rgb{tuple(ec_int[:3])}'
        element = Element(
            'circle', cx=cx, cy=cy, r=r, stroke=stroke, fill=fill, **props
        )
        xml_list.append(element)

    return xml_list, extrema


def shapes_to_xml(data, meta):
    """Generates a xml data for shapes.

    Only two dimensional shapes data is supported. Z ordering of the shapes
    will be taken into account.

    Parameters
    ----------
    data : list of array
        Shapes data. Only two dimensional shapes data is supported.
    meta : dict
        Shapes metadata.

    Returns
    -------
    xml_list : list of xml.etree.ElementTree.Element
        List of xml elements defining each shapes according to the
        svg specification
    extrema : array (2, 2)
        Extrema of data, specified as a minumum then maximum of the (x, y)
        coordinates.
    """
    # Extract metadata parameters
    if 'face_color' in meta:
        face_color = meta['face_color']
    else:
        face_color = np.ones((len(data), 4))

    if 'edge_color' in meta:
        edge_color = meta['edge_color']
    else:
        edge_color = np.zeros((len(data), 4))
        edge_color[:, 3] = 1

    if 'z_index' in meta:
        z_index = meta['z_index']
    else:
        z_index = np.zeros(len(data))

    if 'edge_width' in meta:
        edge_width = meta['edge_width']
    else:
        edge_width = np.ones(len(data))

    if 'opacity' in meta:
        opacity = meta['opacity']
    else:
        opacity = 1

    if 'shape_type' in meta:
        shape_type = meta['shape_type']
    else:
        shape_type = ['rectangle'] * len(data)

    shapes = data

    if len(shapes) > 0:
        # Find extrema of data
        mins = np.min([np.min(d, axis=0) for d in shapes], axis=0)
        maxs = np.max([np.max(d, axis=0) for d in shapes], axis=0)
        extrema = np.array([mins, maxs])
    else:
        extrema = np.full((2, 2), np.nan)

    raw_xml_list = []
    zipped = zip(shapes, shape_type, face_color, edge_color, edge_width)
    for s, st, fc, ec, ew in zipped:
        props = {'stroke-width': str(ew), 'opacity': str(opacity)}
        fc_int = (255 * fc).astype(int)
        props['fill'] = f'rgb{tuple(fc_int[:3])}'
        ec_int = (255 * ec).astype(int)
        props['stroke'] = f'rgb{tuple(ec_int[:3])}'
        shape_to_xml_func = shape_type_to_xml[st]
        element = shape_to_xml_func(s, props)
        raw_xml_list.append(element)

    # reorder according to z-index
    z_order = np.argsort(z_index)
    xml_list = [raw_xml_list[i] for i in z_order]
    return xml_list, extrema


def vectors_to_xml(data, meta):
    """Generates a xml data for vectors.

    Only two dimensional vectors data is supported. Each vector is represented
    by a line.

    Parameters
    ----------
    data : array
        Vectors data. Only two dimensional vectors data is supported.
    meta : dict
        Points metadata.

    Returns
    -------
    xml_list : list of xml.etree.ElementTree.Element
        List of xml elements defining each vector as a line according to the
        svg specification
    extrema : array (2, 2)
        Extrema of data, specified as a minumum then maximum of the (x, y)
        coordinates.
    """
    # Extract metadata parameters
    if 'edge_color' in meta:
        edge_color = meta['edge_color']
    else:
        edge_color = np.zeros((data.shape[0], 4))
        edge_color[:, 3] = 1

    if 'edge_width' in meta:
        edge_width = meta['edge_width']
    else:
        edge_width = 1

    if 'length' in meta:
        length = meta['length']
    else:
        length = 1

    if 'opacity' in meta:
        opacity = meta['opacity']
    else:
        opacity = 1

    # Check if more than 2 dimensional and if so error.
    if data.shape[2] > 2:
        raise ValueError('Vectors must be 2 dimensional to save as svg')
    else:
        vectors = data

    # Find extrema of data
    full_vectors = copy(vectors)
    full_vectors[:, 1, :] = vectors[:, 0, :] + length * vectors[:, 1, :]
    mins = np.min(full_vectors, axis=(0, 1))
    maxs = np.max(full_vectors, axis=(0, 1))
    extrema = np.array([mins, maxs])

    props = {'stroke-width': str(edge_width), 'opacity': str(opacity)}

    xml_list = []
    for v, ec in zip(vectors, edge_color):
        x1 = str(v[0, -2])
        y1 = str(v[0, -1])
        x2 = str(v[0, -2] + length * v[1, -2])
        y2 = str(v[0, -1] + length * v[1, -1])
        ec_int = (255 * ec).astype(int)
        stroke = f'rgb{tuple(ec_int[:3])}'
        props['stroke'] = stroke
        element = Element('line', x1=y1, y1=x1, x2=y2, y2=x2, **props)
        xml_list.append(element)

    return xml_list, extrema
