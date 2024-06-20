from xml.etree.ElementTree import Element
from base64 import b64encode
import numpy as np
from copy import copy
from imageio import imwrite

try:
    from napari.utils.colormaps.colormap_utils import ensure_colormap
except ImportError:  # pragma: no cover
    def ensure_colormap(cmap):
        return _ensure_colormap(cmap)


def _ensure_colormap(cmap):
    from vispy.color import get_colormap
    
    cmap_ = get_colormap(cmap)

    class CmapWrap:
        def __init__(self, cmap):
            self._cmap = cmap

        def map(self, image):
            return self._cmap[image].RGBA/255

    return CmapWrap(cmap_)


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


def layer_transforms_to_xml_string(meta):
    """Get the xml representation[1]_[2]_ of the layer transforms.

    Parameters
    ----------
    meta : dict
        The metadata from the layer.

    Returns
    -------
    tf_list : str
        The transformation list represented as a string.

    References
    ----------
    .. [1] https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/transform
    .. [2] https://www.w3.org/TR/css-transforms-1/
    """
    scale = meta.get('scale', [1, 1])[::-1]
    translate = meta.get('translate', [0, 0])[::-1]
    rotmat = meta.get('rotate', [[1, 0], [0, 1]])
    rotate = np.degrees(np.arctan2(rotmat[0][1], rotmat[1][1]))
    # 'shear' in napari specifies the skew along the y-axis in CSS/SVG, but
    # the latter is in degrees.
    # skew along x can be achieved by combining skewY with a rotation of the
    # same amount.
    # https://www.w3.org/TR/css-transforms-1/#funcdef-transform-skewy
    skewy = np.degrees(np.arctan2(meta.get('shear', [0])[0], 1))
    # matrix elements after converting row-column to y, x, first
    # flipping the rows and then the first two columns of the matrix:
    # a c e   ->   b d f   ->   d b f
    # b d f   ->   a c e   ->   c a e
    d, b, f, c, a, e = np.asarray(meta.get('affine', np.eye(3)))[:-1].ravel()
    strs = [
        f'scale({scale[0]} {scale[1]})',
        f'skewY({skewy})',
        f'rotate({rotate})',
        f'translate({translate[0]} {translate[1]})',
        f'matrix({a} {b} {c} {d} {e} {f})',
    ]
    # Note: transforms are interpreted right-to-left in svg, so must be
    # inverted here.
    return ' '.join(strs[::-1])

def make_linear_matrix_and_offset(meta):
    """Make a transformation matrix from the layer metadata."""
    rotate = np.array(meta.get('rotate', [[1, 0], [0, 1]]))
    shear = np.array([[1, meta.get('shear', [0])[0]], [0, 1]])
    scale = np.diag(meta.get('scale', [1, 1]))
    translate = np.array(meta.get('translate', [0, 0]))
    affine = np.array(meta.get('affine', np.eye(3)))
    linear = affine[:2, :2]
    affine_tr = affine[:2, 2]
    matrix = linear @ (rotate @ shear @ scale)
    offset = linear @ translate + affine_tr
    return matrix, offset


def extrema_coords(coords, meta):
    """Compute the extrema of a set of coordinates after transforms in meta."""
    matrix, offset = make_linear_matrix_and_offset(meta)
    transformed_data = coords @ matrix.T + offset
    return np.array([
        np.min(transformed_data, axis=0), np.max(transformed_data, axis=0)
    ])


def extrema_image(image, meta):
    """Compute the extrema of an image layer, accounting for transforms."""
    coords = np.array([[0, 0], list(image.shape)])
    return extrema_coords(coords, meta)


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
    layer_xml : xml.etree.ElementTree.Element
        Single xml element specifying the image as a png according to
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

    colormap = meta.get('colormap', 'gray')

    if 'opacity' in meta:
        opacity = meta['opacity']
    else:
        opacity = 1

    # Check if data is multiscale, and if so take only last layer
    if multiscale:
        data = data[-1]

    data = np.squeeze(data)

    # Check if more than 2 dimensional and if so error.
    if data.ndim - int(rgb) > 2:
        raise ValueError(f'Image must be 2 dimensional, not {data.ndim - int(rgb)} to save as svg')
    else:
        image = data

    # Find extrema of data
    extrema = extrema_image(image, meta)

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

        cmap = ensure_colormap(colormap)

        # to keep backward compatibility with napari <0.4.18
        # because of a bug in `vmap.map`, we need to ravel, map, then reshape
        mapped_image = (cmap.map(image.ravel()).reshape(image.shape + (4,)) * 255).astype(np.uint8)

    image_str = imwrite('<bytes>', mapped_image, format='png')
    image_str = "data:image/png;base64," + str(b64encode(image_str))[2:-1]
    props = {'xlink:href': image_str}

    width = str(image.shape[1])
    height = str(image.shape[0])

    transform = layer_transforms_to_xml_string(meta)

    layer_xml = Element(
        'image',
        width=width,
        height=height,
        opacity=str(opacity),
        transform=transform,
        **props,
    )

    return layer_xml, extrema


def extrema_points(data, meta):
    """Compute the extrema of points, taking transformations into account."""
    # TODO: account for point sizes below, not just positions
    # could do so by offsetting coordinates along both axes, see for example:
    # https://github.com/scikit-image/scikit-image/blob/fa2a326a734c14b05c25057b03d31c84a6c8a635/skimage/morphology/convex_hull.py#L138-L140
    return extrema_coords(data, meta)


def points_to_xml(data, meta):
    """Generates a xml data for points.

    Only two dimensional points data is supported. Z ordering of the points
    will be taken into account. Each point is represented by a circle. Support
    for other symbols is not yet implemented.

    Note: any shear or anisotropic scaling value will be applied to the
    points, so the markers themselves will be transformed and not perfect
    circles anymore.

    Parameters
    ----------
    data : array
        Points data. Only two dimensional points data is supported.
    meta : dict
        Points metadata.

    Returns
    -------
    layer_xml : xml.etree.ElementTree.Element
        XML group element containing each point according to the
        svg specification.
    extrema : array (2, 2)
        Extrema of data, specified as a minumum then maximum of the (x, y)
        coordinates.
    """
    # Extract metadata parameters
    if 'size' in meta:
        size = meta['size']
        if size.ndim == 2:
            # backward compatibility for napari<v0.4.18 with anisotropic sizes
            size = np.mean(size, axis=1)
    else:
        size = np.ones(data.shape[0])

    if 'face_color' in meta:
        face_color = meta['face_color']
    else:
        face_color = np.ones((data.shape[0], 4))

    if 'border_color' in meta:
        stroke_color = meta['border_color']
    elif 'edge_color' in meta:
        stroke_color = meta['edge_color']
    else:
        stroke_color = np.zeros((data.shape[0], 4))
        stroke_color[:, 3] = 1

    if 'border_width' in meta:
        stroke_width = meta['border_width']
    elif 'edge_width' in meta:
        stroke_width = meta['edge_width']
    else:
        stroke_width = np.ones((data.shape[0],))

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
    extrema = extrema_points(points, meta)

    # Ensure stroke width is an array to handle older versions of
    # napari (e.g. v0.4.0) where it could be a scalar.
    stroke_width = np.broadcast_to(stroke_width, (data.shape[0],)).copy()

    if meta.get('border_width_is_relative') or meta.get('edge_width_is_relative'):
        stroke_width *= size

    transform = layer_transforms_to_xml_string(meta)
    layer_xml = Element('g', transform=transform)

    for p, s, fc, sc, sw in zip(points, size, face_color, stroke_color, stroke_width):
        cx = str(p[1])
        cy = str(p[0])
        r = str(s / 2)
        fc_int = (255 * fc).astype(int)
        fill = f'rgb{tuple(map(int, fc_int[:3]))}'
        sc_int = (255 * sc).astype(int)
        stroke = f'rgb{tuple(map(int, sc_int[:3]))}'
        props = {
            'stroke-width': str(sw),
            'opacity': str(opacity),
        }
        element = Element(
            'circle',
            cx=cx, cy=cy, r=r,
            stroke=stroke,
            fill=fill,
            **props,
        )
        layer_xml.append(element)

    return layer_xml, extrema


def extrema_shapes(shapes_data, meta):
    """Compute the extrema of shapes, taking transformations into account."""
    coords = np.concatenate(shapes_data, axis=0)
    return extrema_coords(coords, meta)


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
    layer_xml : xml.etree.ElementTree.Element
        XML group element containing each shape according to the
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
        extrema = extrema_shapes(shapes, meta)
    else:
        # use nan — these will be discarded when aggregating all layers
        extrema = np.full((2, 2), np.nan)

    transform = layer_transforms_to_xml_string(meta)
    layer_xml = Element('g', transform=transform)
    raw_xml_list = []
    zipped = zip(shapes, shape_type, face_color, edge_color, edge_width)
    for s, st, fc, ec, ew in zipped:
        props = {
            'stroke-width': str(ew),
            'opacity': str(opacity),
        }
        fc_int = (255 * fc).astype(int)
        props['fill'] = f'rgb{tuple(map(int, fc_int[:3]))}'
        ec_int = (255 * ec).astype(int)
        props['stroke'] = f'rgb{tuple(map(int, ec_int[:3]))}'
        shape_to_xml_func = shape_type_to_xml[st]
        element = shape_to_xml_func(s, props)
        raw_xml_list.append(element)

    # reorder according to z-index
    for i in np.argsort(z_index):
        layer_xml.append(raw_xml_list[i])
    return layer_xml, extrema


def extrema_vectors(vectors, meta):
    """Compute the extrema of vectors, taking projections into account."""
    length = meta.get('length', 1)
    start_ends = np.empty(
        (vectors.shape[0] * vectors.shape[1], vectors.shape[-1]),
        dtype=vectors.dtype,
    )
    start_ends[:vectors.shape[0]] = vectors[:, 0, :]
    start_ends[vectors.shape[0]:] = (
        vectors[:, 0, :] + length * vectors[:, 1, :]
    )
    return extrema_coords(start_ends, meta)


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
    layer_xml : xml.etree.ElementTree.Element
        XML group element containing each vector as a line according to the
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
    extrema = extrema_vectors(vectors, meta)

    transform = layer_transforms_to_xml_string(meta)
    layer_xml = Element('g', transform=transform)

    props = {
        'stroke-width': str(edge_width),
        'opacity': str(opacity),
    }
    for v, ec in zip(vectors, edge_color):
        x1 = str(v[0, -2])
        y1 = str(v[0, -1])
        x2 = str(v[0, -2] + length * v[1, -2])
        y2 = str(v[0, -1] + length * v[1, -1])
        ec_int = (255 * ec).astype(int)
        stroke = f'rgb{tuple(map(int, ec_int[:3]))}'
        props['stroke'] = stroke
        element = Element('line', x1=y1, y1=x1, x2=y2, y2=x2, **props)
        layer_xml.append(element)


    return layer_xml, extrema
