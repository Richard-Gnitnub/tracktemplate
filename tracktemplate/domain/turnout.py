"""FreeCAD-independent internal turnout calculations for the inherited host."""


TURNOUT_ORIENTATION_TRAILING = "Trailing against host travel direction"

__all__ = ()


def _turnout_orientation_sign(orientation):
    return -1.0 if str(orientation) == TURNOUT_ORIENTATION_TRAILING else 1.0


def turnout_valid_toe_range(host_length, dimensions, orientation):
    """Return the inherited valid toe interval without normalising its inputs."""
    total = max(0.0, float(host_length))
    start_x = float(dimensions["module_start_x"])
    finish_x = float(dimensions["module_end_x"])
    if _turnout_orientation_sign(orientation) > 0.0:
        minimum = max(0.0, -start_x)
        maximum = min(total, total - finish_x)
    else:
        minimum = max(0.0, finish_x)
        maximum = min(total, total + start_x)
    return minimum, maximum
