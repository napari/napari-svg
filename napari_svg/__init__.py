try:
    from ._version import version as __version__
except ImportError:
    __version__ = "not-installed"


from .hook_implementations import (
    napari_get_writer,
    napari_write_image,
    napari_write_labels,
    napari_write_points,
    napari_write_shapes,
    napari_write_vectors,
)

