import numpy
import json
import pyvista as pv
from typing import Dict
from os.path import splitext, basename
from sdt.utils import write_json
from sdt.constants import (
    KEEP_BY_ALGORITHM,
    KEEP_BY_USER, 
    REMOVE_BY_ALGORITHM,
    REMOVE_BY_USER
)


COLOR_KEEP_BY_ALGORITHM = numpy.array([0.0, 1.0, 0.0])   
COLOR_KEEP_BY_USER = numpy.array([0.0, 0.6, 1.0])   
COLOR_REMOVE_BY_ALGORITHM = numpy.array([1.0, 1.0, 0.0])   
COLOR_REMOVE_BY_USER = numpy.array([1.0, 0.0, 1.0])   


def make_vertex_polydata(pts: numpy.ndarray) -> pv.PolyData:
    """One vertex cell per point + attach original indices to point/cell data."""
    n = pts.shape[0]
    mesh = pv.PolyData(pts)
    verts = numpy.c_[numpy.ones(n, dtype=numpy.int64), numpy.arange(n, dtype=numpy.int64)].ravel()
    mesh.verts = verts
    idx = numpy.arange(n, dtype=numpy.int32)
    mesh.point_data["orig_id"] = idx
    mesh.cell_data["orig_id"]  = idx
    return mesh


def annotations_to_colors(annotations: numpy.ndarray, simple_mode: bool) -> numpy.ndarray:
    colors = numpy.zeros((annotations.shape[0], 3), dtype=numpy.float32)

    if simple_mode:
        mask_remove = numpy.logical_or(annotations == REMOVE_BY_ALGORITHM, annotations == REMOVE_BY_USER)
        mask_keep = numpy.logical_or(annotations == KEEP_BY_ALGORITHM, annotations == KEEP_BY_USER)
        colors[mask_remove] = COLOR_REMOVE_BY_USER
        colors[mask_keep] = COLOR_KEEP_BY_USER
    else:
        colors[annotations == REMOVE_BY_ALGORITHM] = COLOR_REMOVE_BY_ALGORITHM
        colors[annotations == KEEP_BY_ALGORITHM] = COLOR_KEEP_BY_ALGORITHM
        colors[annotations == REMOVE_BY_USER] = COLOR_REMOVE_BY_USER
        colors[annotations == KEEP_BY_USER] = COLOR_KEEP_BY_USER
    
    return colors


def sample_id_from_path(path: str) -> str:
    return splitext(basename(path))[0]


def default_annotation(point_count: int) -> numpy.ndarray:
    return numpy.full((point_count,), KEEP_BY_ALGORITHM, dtype=numpy.uint8)


def load_metadata(json_path: str)-> Dict:
    with open(json_path) as file:
        return json.load(file)


def write_metadata(flags: Dict, json_path: str) -> None:
    write_json(flags, json_path)
