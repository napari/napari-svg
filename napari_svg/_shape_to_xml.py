from xml.etree.ElementTree import Element
import numpy as np


def ellipse_to_xml(data, svg_props):
    """Generates an xml element for an ellipse.

    Only two dimensional ellipses are supported.

    Parameters
    ----------
    data : (4, 2) array
        Ellipse vertices. Only two dimensional ellipses data are supported.
    svg_props : dict
        svg properties for a shape.

    Returns
    -------
    element : xml.etree.ElementTree.Element
        xml element defining an ellipse.
    """
    if data.shape != (4, 2):
        raise ValueError('Ellipse must be 2 dimensional to save as svg')

    data = data[:, ::-1]

    offset = data[1] - data[0]
    angle = -np.arctan2(offset[0], -offset[1])
    if not angle == 0:
        # if shape has been rotated, shift to origin
        cen = data.mean(axis=0)
        coords = data - cen

        # rotate back to axis aligned
        c, s = np.cos(angle), np.sin(-angle)
        rotation = np.array([[c, s], [-s, c]])
        coords = coords @ rotation.T

        # shift back to center
        coords = coords + cen

        # define rotation around center
        transform = f'rotate({np.degrees(-angle)} {cen[0]} {cen[1]})'
        svg_props['transform'] = transform
    else:
        coords = data

    cx = str(cen[0])
    cy = str(cen[1])
    size = abs(coords[2] - coords[0])
    rx = str(size[0] / 2)
    ry = str(size[1] / 2)

    element = Element('ellipse', cx=cx, cy=cy, rx=rx, ry=ry, **svg_props)
    return element


def line_to_xml(data, svg_props):
    """Generates an xml element for a line.

    Only two dimensional lines are supported.

    Parameters
    ----------
    data : (2, 2) array
        Line vertices. Only two dimensional lines data are supported.
    svg_props : dict
        svg properties for a shape.

    Returns
    -------
    element : xml.etree.ElementTree.Element
        xml element defining a line.
    """
    if data.shape != (2, 2):
        raise ValueError('Line must be 2 dimensional to save as svg')

    x1 = str(data[0, 0])
    y1 = str(data[0, 1])
    x2 = str(data[1, 0])
    y2 = str(data[1, 1])

    element = Element('line', x1=y1, y1=x1, x2=y2, y2=x2, **svg_props)
    return element


def path_to_xml(data, svg_props):
    """Generates an xml element for a path.

    Only two dimensional paths are supported.

    Parameters
    ----------
    data : (N, 2) array
        Path vertices. Only two dimensional paths data are supported.
    svg_props : dict
        svg properties for a shape.

    Returns
    -------
    element : xml.etree.ElementTree.Element
        xml element defining a polyline.
    """
    if data.shape[1] != 2:
        raise ValueError('Path must be 2 dimensional to save as svg')

    points = ' '.join([f'{d[1]},{d[0]}' for d in data])
    
    svg_props['fill'] = 'none'

    element = Element('polyline', points=points, **svg_props)
    return element


def polygon_to_xml(data, svg_props):
    """Generates an xml element for a polygon.

    Only two dimensional polygons are supported.

    Parameters
    ----------
    data : (N, 2) array
        Polygon vertices. Only two dimensional polygons data are supported.
    svg_props : dict
        svg properties for a shape.

    Returns
    -------
    element : xml.etree.ElementTree.Element
        xml element defining a polygon.
    """

    if data.shape[1] != 2:
        raise ValueError('Polygon must be 2 dimensional to save as svg')

    points = ' '.join([f'{d[1]},{d[0]}' for d in data])
    
    element = Element('polygon', points=points, **svg_props)
    return element


def rectangle_to_xml(data, svg_props):
    """Generates an xml element for a rectangle.

    Only two dimensional rectangles are supported.

    Parameters
    ----------
    data : (N, 2) array
        Rectangle vertices. Only two dimensional rectangles data are supported.
    svg_props : dict
        svg properties for a shape.

    Returns
    -------
    element : xml.etree.ElementTree.Element
        xml element defining a rect.
    """
    if data.shape != (4, 2):
        raise ValueError('Rectangle must be 2 dimensional to save as svg')

    data = data[:, ::-1]

    offset = data[1] - data[0]
    angle = -np.arctan2(offset[0], -offset[1])
    if not angle == 0:
        # if shape has been rotated, shift to origin
        cen = data.mean(axis=0)
        coords = data - cen

        # rotate back to axis aligned
        c, s = np.cos(angle), np.sin(-angle)
        rotation = np.array([[c, s], [-s, c]])
        coords = coords @ rotation.T

        # shift back to center
        coords = coords + cen

        # define rotation around center
        transform = f'rotate({np.degrees(-angle)} {cen[0]} {cen[1]})'
        svg_props['transform'] = transform
    else:
        coords = data

    x = str(coords.min(axis=0)[0])
    y = str(coords.min(axis=0)[1])
    size = abs(coords[2] - coords[0])
    width = str(size[0])
    height = str(size[1])

    element = Element(
        'rect', x=x, y=y, width=width, height=height, **svg_props
    )
    return element
