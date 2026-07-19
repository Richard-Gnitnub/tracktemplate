"""Shared real-FreeCAD measurements for plain-line export artifacts."""

import pathlib

import Mesh
import Part


def _rounded(value, places=9):
    result = round(float(value), places)
    return 0.0 if result == 0.0 else result


def _bounds(bound_box):
    return {
        "XMin": _rounded(bound_box.XMin),
        "XMax": _rounded(bound_box.XMax),
        "XLength": _rounded(bound_box.XLength),
        "YMin": _rounded(bound_box.YMin),
        "YMax": _rounded(bound_box.YMax),
        "YLength": _rounded(bound_box.YLength),
        "ZMin": _rounded(bound_box.ZMin),
        "ZMax": _rounded(bound_box.ZMax),
        "ZLength": _rounded(bound_box.ZLength),
    }


def format_export_metrics(module, directory, variant, shape_summary):
    """Measure exported bounds, topology and mesh statistics in real FreeCAD."""
    metrics = {}
    for relative_name in sorted(variant.get("files", {})):
        path = pathlib.Path(directory) / relative_name
        logical_name = variant["files"][relative_name]["logical_name"]
        suffix = path.suffix.lower()
        if suffix == ".dxf":
            values = module.validate_dxf_export_bounds(str(path))
            metrics[logical_name] = {
                "format": "dxf",
                "bounds": {key: _rounded(value) for key, value in values.items()},
            }
        elif suffix == ".svg":
            values = module.validate_svg_export_bounds(str(path))
            metrics[logical_name] = {
                "format": "svg",
                "bounds": {key: _rounded(value) for key, value in values.items()},
            }
        elif suffix == ".stl":
            mesh = Mesh.Mesh(str(path))
            metrics[logical_name] = {
                "format": "stl",
                "facets": int(mesh.CountFacets),
                "points": int(mesh.CountPoints),
                "bounds_mm": _bounds(mesh.BoundBox),
                "volume_mm3": _rounded(getattr(mesh, "Volume", 0.0)),
            }
        elif suffix == ".step":
            shape = Part.Shape()
            shape.read(str(path))
            metrics[logical_name] = {
                "format": "step",
                "shape": shape_summary(shape),
            }
    return metrics
