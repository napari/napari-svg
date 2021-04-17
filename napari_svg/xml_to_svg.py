from xml.etree.ElementTree import Element, tostring

import numpy as np


def xml_to_svg(xml_list, extrema):
    """Convert a list of xml into an SVG string.

    Parameters
    ----------
    xml_list : list of xml.etree.ElementTree.Element
        List of a xml elements in the svg specification.
    extrema : array (2, 2)
        Extrema of data, specified as a minumum then maximum of the (x, y)
        coordinates. Used to specify the view box of SVG canvas.

    Returns
    -------
    svg : string
        SVG representation of the layer.
    """

    extrema = np.nan_to_num(extrema)

    corner = extrema[0]
    shape = extrema[1] - extrema[0]

    # set any 0 values in the shape to 1 to prevent height or width = 0
    # see: https://github.com/napari/napari-svg/pull/12
    shape[shape == 0] = 1

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
