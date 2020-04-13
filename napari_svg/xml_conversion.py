from xml.etree.ElementTree import Element, tostring
from base64 import b64encode
import numpy as np
from imageio import imwrite
from vispy.color import get_colormap


def xml_to_svg(xml_list, extrema):
    """Convert a list of xml into an SVG string.

    Parameters
    ----------
    xml : list of xml.etree.ElementTree.Element
        List of a xml elements in the svg specification.
    extrema : array (2, 2)
        Extrema of data, specified as a minumum then maximum of the (x, y)
        coordinates. Used to specify the view box of SVG canvas.

    Returns
    ----------
    svg : string
        SVG representation of the layer.
    """

    corner = extrema[0]
    shape = extrema[1] - extrema[0]

    props = {
        'xmlns': 'http://www.w3.org/2000/svg',
        'xmlns:xlink': 'http://www.w3.org/1999/xlink',
    }

    xml = Element(
        'svg',
        height=f'{shape[0]}',
        width=f'{shape[1]}',
        version='1.1',
        **props,
    )

    transform = f'translate({-corner[1]} {-corner[0]})'
    xml_transform = Element('g', transform=transform)
    for x in xml_list:
        xml_transform.append(x)
    xml.append(xml_transform)

    svg = (
        '<?xml version=\"1.0\" standalone=\"no\"?>\n'
        + '<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\"\n'
        + '\"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n'
        + tostring(xml, encoding='unicode', method='xml')
    )

    return svg


def image_to_xml(data, meta):
    """Generates a xml data for an image.

    Only two dimensional data (including rgb, and pyramid) is supported. For
    pyramid data the lowest resolution is used.

    The xml data is a list with a single xml element that defines the
    currently viewed image as a png according to the svg specification.

    Parameters
    ----------
    data : array or list of array
        Image data. Only two dimensional data (including rgb, and pyramid) is
        supported. For pyramid data the lowest resolution is used.
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
    # Check if data is a pyramid, and if so take only last layer
    if meta['is_pyramid']:
        data = data[-1]

    # Check if more than 2 dimensional and if so error.
    if data.ndim - int(meta['rgb']) > 2:
        raise ValueError('Data must be 2 dimensional to save to svg')
    else:
        image = data

    # Find extrema of data
    extrema = np.array([[0, 0], [image.shape[0], image.shape[1]]])

    # Extract used metadata parameters
    contrast_limits = meta['contrast_limits']
    colormap_name = meta['colormap']
    opacity=str(meta['opacity'])

    if meta['rgb']:
        mapped_image = image
    else:
        # apply contrast_limits to data
        image = np.clip(
            image, contrast_limits[0], contrast_limits[1]
        )
        image = image - contrast_limits[0]
        color_range = contrast_limits[1] - contrast_limits[0]
        if color_range != 0:
            data = data / color_range

        # get colormap
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
        'image', width=width, height=height, opacity=opacity, **props
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
    # Check if more than 2 dimensional and if so error.
    if data.shape[1] > 2:
        raise ValueError('Data must be 2 dimensional to save to svg')
    else:
        points = data

    # Find extrema of data
    extrema = np.array([points.min(axis=0), points.max(axis=0)])

    # Extract used metadata parameters
    size = np.mean(meta['size'], axis=1)
    face_color = meta['face_color']
    edge_color = meta['edge_color']
    edge_width = str(meta['edge_width'])
    opacity=str(meta['opacity'])

    props = {'stroke-width': edge_width, 'opacity': opacity}

    xml_list = []
    for p, s, fc, ec in zip(points, size, face_color, edge_color):
        cx = str(p[1])
        cy = str(p[0])
        r = str(s / 2)
        face_color = (255 * fc).astype(np.int)
        fill = f'rgb{tuple(face_color[:3])}'
        edge_color = (255 * ec).astype(np.int)
        stroke = f'rgb{tuple(edge_color[:3])}'
        element = Element(
            'circle', cx=cx, cy=cy, r=r, stroke=stroke, fill=fill, **props
        )
        xml_list.append(element)

    return xml_list, extrema
