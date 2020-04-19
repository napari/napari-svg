import os
import numpy as np
from napari_svg import napari_write_image
from napari.layers import Image


def test_write_image_no_metadata(tmpdir):
    """Test writing image data with no metadata."""
    data = np.random.rand(20, 20)
    meta = {}

    path = os.path.join(tmpdir, 'image_file.svg')

    # Check file does not exist
    assert not os.path.isfile(path)

    # Write data
    assert napari_write_image(path, data, meta)

    # Check file now exists
    assert os.path.isfile(path)


def test_write_image_from_napari_layer_data(tmpdir):
    """Test writing image data from napari layer_data tuple."""
    data = np.random.rand(20, 20)
    layer = Image(data)
    layer_data = layer.as_layer_data_tuple()

    path = os.path.join(tmpdir, 'image_file.svg')

    # Check file does not exist
    assert not os.path.isfile(path)

    # Write data
    assert napari_write_image(path, layer_data[0], layer_data[1])

    # Check file now exists
    assert os.path.isfile(path)


def test_write_image_no_extension(tmpdir):
    """Test writing image data with no extension."""
    data = np.random.rand(20, 20)
    layer = Image(data)
    layer_data = layer.as_layer_data_tuple()

    path = os.path.join(tmpdir, 'image_file')

    # Check file does not exist
    assert not os.path.isfile(path)

    # Write data
    assert napari_write_image(path, layer_data[0], layer_data[1])

    # Check file now exists with an svg extension
    assert os.path.isfile(path + '.svg')


def test_no_write_image_bad_extension(tmpdir):
    """Test not writing image data with a bad extension."""
    data = np.random.rand(20, 20)
    layer = Image(data)
    layer_data = layer.as_layer_data_tuple()

    path = os.path.join(tmpdir, 'image_file.csv')

    # Check file does not exist
    assert not os.path.isfile(path)

    # Check no data is writen
    assert not napari_write_image(path, layer_data[0], layer_data[1])

    # Check file still does not exist
    assert not os.path.isfile(path)
