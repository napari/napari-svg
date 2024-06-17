import os
import numpy as np
import pytest
from pathlib import Path
from napari.layers import Image, Points, Labels, Shapes, Vectors
from napari.utils.colormaps.colormap_utils import ensure_colormap
from napari_svg.layer_to_xml import layer_transforms_to_xml_string
from napari_svg import (
    napari_write_image,
    napari_write_labels,
    napari_write_points,
    napari_write_shapes,
    napari_write_vectors,
)

from napari_svg.layer_to_xml import _ensure_colormap


@pytest.fixture(params=['image', 'labels', 'points', 'shapes', 'shapes-rectangles', 'vectors'])
def layer_writer_and_data(request):
    meta_required = False
    if request.param == 'image':
        data = np.random.rand(20, 20)
        layer = Image(data)
        writer = napari_write_image
    elif request.param == 'labels':
        data = np.random.randint(10, size=(20, 20))
        layer = Labels(data)
        writer = napari_write_labels
    elif request.param == 'points':
        data = np.random.rand(20, 2)
        layer = Points(data)
        writer = napari_write_points
    elif request.param == 'shapes':
        np.random.seed(0)
        data = [
            np.random.rand(2, 2),
            np.random.rand(2, 2),
            np.random.rand(6, 2),
            np.random.rand(6, 2),
            np.random.rand(2, 2),
        ]
        shape_type = ['ellipse', 'line', 'path', 'polygon', 'rectangle']
        layer = Shapes(data, shape_type=shape_type)
        writer = napari_write_shapes
        meta_required = True
    elif request.param == 'shapes-rectangles':
        np.random.seed(0)
        data = np.random.rand(7, 4, 2)
        layer = Shapes(data)
        writer = napari_write_shapes
    elif request.param == 'vectors':
        data = np.random.rand(20, 2, 2)
        layer = Vectors(data)
        writer = napari_write_vectors
    else:
        return None, None, False
    
    layer_data = layer.as_layer_data_tuple()
    return writer, layer_data, meta_required


def test_write_layer_no_metadata(tmpdir, layer_writer_and_data):
    """Test writing layer data with no metadata."""
    writer, layer_data, meta_required = layer_writer_and_data
    if meta_required:
        return

    path = os.path.join(tmpdir, 'layer_file.svg')
    
    # Check file does not exist
    assert not os.path.isfile(path)

    # Write data
    return_path =  writer(path, layer_data[0], {})
    assert return_path == path

    # Check file now exists
    assert os.path.isfile(path)


def test_write_image_from_napari_layer_data(tmpdir, layer_writer_and_data):
    """Test writing layer data from napari layer_data tuple."""
    writer, layer_data, _ = layer_writer_and_data
    path = os.path.join(tmpdir, 'layer_file.svg')

    # Check file does not exist
    assert not os.path.isfile(path)

    # Write data
    return_path = writer(path, layer_data[0], layer_data[1])
    assert return_path == path

    # Check file now exists
    assert os.path.isfile(path)


def test_write_image_no_extension(tmpdir, layer_writer_and_data):
    """Test writing layer data with no extension."""
    writer, layer_data, _ = layer_writer_and_data
    path = os.path.join(tmpdir, 'layer_file')

    # Check file does not exist
    assert not os.path.isfile(path)

    # Write data
    return_path = writer(path, layer_data[0], layer_data[1])
    assert return_path == path + '.svg'

    # Check file now exists with an svg extension
    assert os.path.isfile(path + '.svg')


def test_no_write_image_bad_extension(tmpdir, layer_writer_and_data):
    """Test not writing layer data with a bad extension."""
    writer, layer_data, _ = layer_writer_and_data
    path = os.path.join(tmpdir, 'layer_file.csv')

    # Check file does not exist
    assert not os.path.isfile(path)

    # Check no data is writen
    return_path = writer(path, layer_data[0], layer_data[1])
    assert return_path is None

    # Check file still does not exist
    assert not os.path.isfile(path)


@pytest.mark.parametrize('colormap', ('viridis', ensure_colormap('viridis').dict()))
def test_write_image_colormaps(tmpdir, layer_writer_and_data, colormap):
    writer, layer_data, _ = layer_writer_and_data
    layer_data[1]['colormap'] = colormap

    path = os.path.join(tmpdir, 'layer_file.svg')

    # Check file does not exist
    assert not os.path.isfile(path)

    # Write data
    return_path = writer(path, layer_data[0], layer_data[1])
    assert return_path == path

    # Check file now exists
    assert os.path.isfile(path)


@pytest.mark.parametrize("path_ensure", [True, False])
def test_write_image_colormaps_vispy(tmpdir, layer_writer_and_data, path_ensure, monkeypatch):
    if path_ensure:
        monkeypatch.setattr("napari_svg.layer_to_xml.ensure_colormap", _ensure_colormap)
    writer, layer_data, _ = layer_writer_and_data
    layer_data[1]['colormap'] = "autumn"

    path = os.path.join(tmpdir, 'layer_file.svg')

    # Check file does not exist
    assert not os.path.isfile(path)

    # Write data
    return_path = writer(path, layer_data[0], layer_data[1])
    assert return_path == path

    # Check file now exists
    assert os.path.isfile(path)


NOOP_TRANSFORM = layer_transforms_to_xml_string({
    'scale': [1.0, 1.0],
    'translate': [0.0, 0.0],
    'shear': [0.0],
    'rotate': [[1.0, 0.0], [0.0, 1.0]],
    'affine': [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
})
NOOP_TRANSFORM_STR = f' transform="{NOOP_TRANSFORM}"'

def test_write_points_with_attributes(request, tmp_path):
    data = [
        [0, 0],
        [0, 128],
        [128, 128],
    ]
    size = [16, 20, 24]
    face_color = ['red', 'green', 'blue']
    edge_color = ['cyan', 'magenta', 'yellow']
    edge_width = [0.05, 0.25, 0.5]
    layer = Points(
        data,
        opacity=0.5,
        size=size,
        face_color=face_color,
        edge_color=edge_color,
        edge_width=edge_width,
        edge_width_is_relative=True,
    )
    test_name = request.node.name
    path = tmp_path / f'{test_name}-actual.svg'
    layer_data, layer_attrs, _ = layer.as_layer_data_tuple()

    return_path = napari_write_points(path, layer_data, layer_attrs)
    assert return_path == path

    expected_path = Path(__file__).parent / f'{test_name}-expected.svg'
    actual_text = path.read_text().replace(NOOP_TRANSFORM_STR, '')
    expected_text = expected_path.read_text().replace(NOOP_TRANSFORM_STR, '')
    assert actual_text == expected_text