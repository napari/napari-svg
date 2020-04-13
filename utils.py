import os
from imageio import imwrite


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


def image_to_xml_list(image, rgb=False, contrast_limits=[0, 1], colormap='gray', opacity=1):
    """Generates a list with a single xml element that defines the
    currently viewed image as a png according to the svg specification.

    Treat rgb image data as rgb. For data with dimensionality bigger than 2
    take a maximum intensity project across. For pyramid data take the lowest
    resolution.

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
    xml : list of xml.etree.ElementTree.Element
        List of a single xml element specifying the currently viewed image
        as a png according to the svg specification.
    """

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
            data = data / color_range

        # create colormap
        
    
        # apply colormap to data
        mapped_image = colormap[image.ravel()]
        mapped_image = mapped_image.RGBA.reshape(image.shape + (4,))

    image_str = imwrite('<bytes>', mapped_image, format='png')
    image_str = "data:image/png;base64," + str(b64encode(image_str))[2:-1]
    props = {'xlink:href': image_str}

    width = str(image.shape[1])
    height = str(image.shape[0])
    opacity = str(opacity)

    xml = Element(
        'image', width=width, height=height, opacity=opacity, **props
    )
    return [xml]
