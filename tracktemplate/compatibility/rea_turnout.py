"""Prepare explicit source B/C geometry without changing a FreeCAD document.

The inherited host owns host admission, mapping and connector construction.
This adapter supplies one explicit source specification to those operations.
Its results are transient research records, not legacy creation configurations.
"""

from dataclasses import asdict, dataclass
import math

from tracktemplate.domain import rea_turnout
from tracktemplate.domain.crossover import complete_radius_decision
from tracktemplate.compatibility.rea_turnout_rails import (
    rea_turnout_rail_polylines,
)


@dataclass(frozen=True)
class ReaTurnoutGeometryAdapter:
    """Share source calculations between TO preparation and both XO legs."""

    module: object

    def _host(self, host):
        module = self.module
        if not module.is_turnout_host_centreline(host):
            raise ValueError("Select a recognised generated track centreline.")
        set_id = module.object_string_property(host, "TemplateSetID", "")
        if not set_id:
            raise ValueError("The host has no template-set identity.")
        return module.turnout_host_alignment(host), set_id

    def _placement(self, data, dimensions, toe, handing, orientation):
        module = self.module
        if handing not in (module.TURNOUT_HAND_LEFT, module.TURNOUT_HAND_RIGHT):
            raise ValueError("Turnout handing must be Left-hand or Right-hand.")
        if orientation not in (
            module.TURNOUT_ORIENTATION_FACING,
            module.TURNOUT_ORIENTATION_TRAILING,
        ):
            raise ValueError("Turnout orientation is not recognised.")
        toe = float(toe)
        if not math.isfinite(toe):
            raise ValueError("Switch-toe chainage must be finite.")
        lower, upper = module.turnout_valid_toe_range(
            data["total"], dimensions, orientation,
        )
        if upper < lower - module.GEOMETRY_TOLERANCE:
            raise ValueError("The host is too short for this turnout module.")
        if toe < lower - 1.0e-7 or toe > upper + 1.0e-7:
            raise ValueError("Switch-toe chainage is outside the host interval.")
        return toe

    def _turnout(self, doc, host, toe, handing, orientation, spec, dimensions):
        module = self.module
        data, set_id = self._host(host)
        toe = self._placement(data, dimensions, toe, handing, orientation)
        conflict, overlap = module._turnout_find_overlap(
            doc, host, toe, dimensions, orientation,
        )
        if conflict is not None:
            raise ValueError(
                "The source turnout overlaps an existing turnout by "
                "{:.3f} mm.".format(overlap)
            )
        mapping = module.turnout_mapping_metrics(
            data, toe, orientation, handing, dimensions,
        )
        rails = []
        for name, local in rea_turnout_rail_polylines(module, dimensions):
            points = module._turnout_map_polyline(
                data, toe, orientation, handing, local,
            )
            module._turnout_validate_mapped_polyline(points, name)
            rails.append({"name": name, "local_points": local, "points": points})
        width, _thickness = module.turnout_host_template_dimensions(doc, host)
        timbers = []
        for station in rea_turnout.rea_turnout_timber_stations(spec):
            timber = dict(station)
            timber.update(module._turnout_timber_end_data(
                dimensions, timber["x"], width,
            ))
            local = module._turnout_timber_outline_local_points(timber)
            points = module._turnout_map_polyline(
                data, toe, orientation, handing, local,
            )
            module._turnout_validate_mapped_polyline(
                points, "Timber " + timber["identifier"],
            )
            timber.update(local_points=local, points=points)
            timbers.append(timber)
        return {
            "status": "transient-only",
            "source_specification": asdict(spec),
            "host_identity": {"object_name": str(host.Name),
                              "template_set_id": set_id},
            "toe_chainage": toe, "handing": handing,
            "orientation": orientation, "dimensions": dimensions,
            "mapping": mapping, "rails": rails, "timbers": timbers,
            "host_station_interval": module.turnout_host_station_interval(
                toe, dimensions, orientation,
            ),
            "qualification_gaps": tuple(dimensions["source_gaps"]) + (
                "Document creation, editing and persistence are not admitted.",
                "Chair placement and physical fit are not qualified.",
                "Native and GUI qualification remain pending.",
                "Timber lengths use the inherited template envelope; "
                "source production lengths remain unqualified.",
            ),
        }

    def turnout(self, doc, host, toe, handing, orientation, specification):
        """Return actual mapped source rails and timbers without mutation."""
        dimensions = rea_turnout.rea_turnout_dimensions(specification)
        return self._turnout(
            doc, host, toe, handing, orientation, specification, dimensions,
        )

    def crossover(
        self, doc, host_a, host_b, reference_chainage, specification, *,
        arrangement=None, handing=None, minimum_radius=None,
    ):
        """Resolve one source specification through both roads and connector."""
        module = self.module
        dimensions = rea_turnout.rea_turnout_dimensions(specification)
        data_a, set_a = self._host(host_a)
        data_b, set_b = self._host(host_b)
        if host_a.Name == host_b.Name:
            raise ValueError("Crossover hosts must be different centrelines.")
        if set_a != set_b:
            raise ValueError("Crossover hosts must belong to one template set.")
        if arrangement is None:
            arrangement = module.CROSSOVER_ARRANGEMENT_FACING
        if arrangement not in (module.CROSSOVER_ARRANGEMENT_FACING,
                                module.CROSSOVER_ARRANGEMENT_TRAILING):
            raise ValueError("Crossover arrangement must be facing or trailing.")
        if minimum_radius is None:
            minimum_radius = module.CROSSOVER_DEFAULT_MINIMUM_RADIUS
        minimum_radius = float(minimum_radius)
        if (not math.isfinite(minimum_radius)
                or minimum_radius < module.CROSSOVER_MINIMUM_ALLOWED_RADIUS):
            raise ValueError("Minimum resulting radius is outside the allowed range.")
        orientation_a = (
            module.TURNOUT_ORIENTATION_FACING
            if arrangement == module.CROSSOVER_ARRANGEMENT_FACING
            else module.TURNOUT_ORIENTATION_TRAILING
        )
        toe_a = self._placement(
            data_a, dimensions, reference_chainage,
            module.TURNOUT_HAND_LEFT, orientation_a,
        )
        automatic = module._crossover_automatic_hand(
            data_a, data_b, toe_a, orientation_a,
        )
        if handing is None or handing == module.CROSSOVER_HAND_AUTO:
            handing = automatic
        if handing != automatic:
            raise ValueError("The selected handing turns away from Host Track B.")
        orientation_b, _projected, cosine = module._crossover_orientation_b(
            data_a, data_b, toe_a, orientation_a,
        )
        point_a, _heading = module.interpolate_alignment_station(data_a, toe_a)
        _station, _point, _heading, separation = (
            module._crossover_nearest_point_on_alignment(data_b, point_a)
        )
        if separation > module.CROSSOVER_MAXIMUM_TRACK_SEPARATION:
            raise ValueError("Track separation exceeds the crossover solver limit.")
        if abs(cosine) < math.cos(math.radians(30.0)):
            raise ValueError("Crossover hosts are not sufficiently near-parallel.")
        solved = module._crossover_solve_toe_b(
            data_a, data_b, toe_a, orientation_a, orientation_b, handing,
            dimensions, minimum_radius,
        )
        road_a = self._turnout(doc, host_a, toe_a, handing, orientation_a,
                               specification, dimensions)
        road_b = self._turnout(doc, host_b, solved["toe_b"], handing,
                               orientation_b, specification, dimensions)
        for host, road in ((host_a, road_a), (host_b, road_b)):
            conflict, _overlap = module._crossover_find_existing_conflict(
                doc, host, road["host_station_interval"], None,
            )
            if conflict is not None:
                raise ValueError("The source turnout overlaps an existing crossover.")
        decision = complete_radius_decision(
            road_a["mapping"]["turnout_minimum_radius"],
            road_b["mapping"]["turnout_minimum_radius"],
            solved["connector"].get("minimum_radius"), minimum_radius,
        )
        if not decision["accepted"]:
            raise ValueError(decision["diagnostic"])
        # Deliberately not a legacy pre_solved payload: that path cannot
        # create new source geometry with fixed C10 dimensions or timbering.
        return {
            "status": "transient-only",
            "source_specification": asdict(specification),
            "turnout_a": road_a, "turnout_b": road_b,
            "connector": solved["connector"], "radius_assessment": decision,
            "qualification_gaps": road_a["qualification_gaps"],
        }
