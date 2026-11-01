"""Explicit stored B/C commands using the retained analytical host engine.

The injected document store owns transactions; the injected scene factory
owns rendering types. This boundary creates no exact Part geometry.
"""

from dataclasses import dataclass
import hashlib
import json
import math

from tracktemplate.application.rea_turnout_state import (
    ReaTrackworkIntent,
    REA_INTENT_JSON_PROPERTY,
    rea_trackwork_geometry_signature,
    rea_trackwork_intent_to_json,
)
from tracktemplate.compatibility.rea_trackwork_admission import source_records
from tracktemplate.compatibility.rea_turnout import ReaTurnoutGeometryAdapter
from tracktemplate.domain.crossover import complete_radius_decision


def _require(condition, message):
    if not condition:
        raise ValueError("REA research trackwork: " + message)


def _pairs(items):
    result = {}
    for key, value in items:
        _require(key not in result, "duplicate stored JSON field")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError("Nonfinite stored JSON: " + value)


def _json(text):
    _require(type(text) is str and bool(text), "stored JSON is missing")
    return json.loads(text, object_pairs_hook=_pairs,
                      parse_constant=_invalid_constant)


def _digest(value):
    text = json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _number(value):
    _require(type(value) in (int, float), "finite numeric input required")
    number = float(value)
    _require(math.isfinite(number), "nonfinite numeric input")
    return number


def _point(point):
    return tuple(_number(value) for value in (point.x, point.y, point.z))


@dataclass(frozen=True)
class _PreparedTrackwork:
    owner: object
    document: object
    intent: ReaTrackworkIntent
    hosts: tuple
    scene: object
    signature: str
    existing: object
    previous_payload: object
    dependencies: tuple


class ReaTrackworkWorkflow:
    """Prepare, commit and rebuild one explicit source-qualified TO/XO."""

    def __init__(self, module, store, scene_factory):
        self.module = module
        self.store = store
        self.scene_factory = scene_factory
        self._geometry = ReaTurnoutGeometryAdapter(module)
        self._owner = object()
        self._prepared = None

    def _hosts(self, document, intent):
        module = self.module
        result = []
        for name in intent.host_names:
            host = document.getObject(name)
            _require(host is not None and host.Document is document
                     and host.Name == name, "host locator is missing or changed")
            _require(module.is_turnout_host_centreline(host),
                     "host is not an admitted generated centreline")
            _require(module.object_string_property(host, "TemplateSetID", "")
                     == intent.template_set_id, "host template-set mismatch")
            _require(module.object_string_property(host, "GeneratedBy", "")
                     == module.GENERATOR_ID, "host generator mismatch")
            result.append(host)
        _require(len({id(host) for host in result}) == len(result),
                 "host locators must identify different objects")
        return tuple(result)

    def _host_state(self, document, host):
        module = self.module
        set_id = module.object_string_property(host, "TemplateSetID", "")
        settings = module.settings_for_template_set(document, set_id)
        owners = [obj for obj in document.Objects
                  if module.is_generated_settings(obj)
                  and module.object_string_property(obj, "TemplateSetID", "")
                  == set_id]
        _require(len(owners) == 1 and owners[0] is settings,
                 "a unique same-set host settings object is required")
        values = {}
        for field in ("TransitionLength", "CurveRadius", "TotalTurnAngle",
                      "MainTemplateWidth", "TemplateThickness"):
            values[field] = _number(module.quantity_value(
                settings, field, math.nan,
            ))
        _require(values["MainTemplateWidth"] > 0
                 and values["TemplateThickness"] > 0,
                 "host width and thickness must be positive")
        tracks_text = getattr(settings, "TrackConfigurationJSON", None)
        straights_text = getattr(settings, module.STRAIGHT_CONFIGS_PROPERTY,
                                 None)
        tracks, straights = _json(tracks_text), _json(straights_text)
        _require(type(tracks) is list and type(straights) is list,
                 "canonical host configuration lists are required")
        route_id = module.object_string_property(host, "RouteID", "")
        number = module._integer_object_property(host, "TrackNumber", 0)
        _require(type(number) is int and number >= 1,
                 "host track number is invalid")
        if route_id:
            routes = [item for item in straights if type(item) is dict
                      and item.get("manager_id") == route_id]
            _require(len(routes) == 1, "host route is missing or ambiguous")
            _require(_number(routes[0].get("template_width")) > 0
                     and _number(routes[0].get("template_thickness")) > 0,
                     "route dimensions are invalid")
        elif number > 1:
            _require(number - 2 < len(tracks)
                     and type(tracks[number - 2]) is dict,
                     "host track configuration is missing")
            _require(_number(tracks[number - 2].get("width")) > 0,
                     "host track width is invalid")
        values.update(track_configuration=tracks_text,
                      straight_configuration=straights_text,
                      settings_name=str(settings.Name))
        data = module.turnout_host_alignment(host)
        identity = {field: module.object_string_property(host, field, "")
                    for field in ("GeneratedBy", "GeneratedRole",
                                  "TemplateSetID", "RouteID", "RouteName",
                                  "TrackName", "ExportSubtype")}
        identity.update(object_name=str(host.Name), track_number=number,
                        canonical_settings=values)
        identity["geometry"] = {
            "total": _number(data["total"]),
            "stations": tuple(_number(x) for x in data["stations"]),
            "headings": tuple(_number(x) for x in data["headings"]),
            "points": tuple(_point(p) for p in data["points"]),
        }
        return {"object_name": host.Name, "template_set_id": set_id,
                "state_signature": _digest(identity)}

    def _legacy_records(self, document):
        module = self.module
        result = []
        identities = set()
        roles = (
            (module.TURNOUT_SETTINGS_ROLE,
             module.TURNOUT_CONFIGURATION_PROPERTY, "turnout", "turnout_id"),
            (module.CROSSOVER_SETTINGS_ROLE,
             module.CROSSOVER_CONFIGURATION_PROPERTY, "crossover",
             "crossover_id"),
        )
        for obj in document.Objects:
            role = module.object_string_property(obj, "GeneratedRole", "")
            for expected, field, kind, id_field in roles:
                if role != expected:
                    continue
                text = getattr(obj, field, None)
                config = _json(text)
                _require(type(config) is dict, "legacy occupancy is malformed")
                _require(module.object_string_property(obj, "GeneratedBy", "")
                         == module.GENERATOR_ID
                         and module.object_string_property(
                             obj, "TemplateSetID", "",
                         ) == config.get("template_set_id"),
                         "legacy settings ownership is inconsistent")
                self._legacy_context(config, kind)
                identifier = config.get(id_field)
                _require(type(identifier) is str and identifier
                         and identifier not in identities,
                         "legacy occupancy identity is missing or duplicated")
                identities.add(identifier)
                result.append((kind, identifier, config, text))
        return tuple(sorted(result, key=lambda item: (item[0], item[1])))

    def _legacy_context(self, config, kind):
        module = self.module
        _require(type(config) is dict, "legacy occupancy is malformed")
        schema = getattr(module, kind.upper() + "_SCHEMA_VERSION")
        source = getattr(module, kind.upper() + "_SOURCE_NOTE")
        _require(type(config.get("schema_version")) is int
                 and config["schema_version"] == schema
                 and config.get("size") == module.TURNOUT_SIZE_C10
                 and config.get("source") == source
                 and "source_specification" not in config,
                 "legacy source context is unsupported")
        _require(type(config.get("template_set_id")) is str
                 and bool(config["template_set_id"]),
                 "legacy template-set identity is missing")
        _require(config.get("handing") in (module.TURNOUT_HAND_LEFT,
                                           module.TURNOUT_HAND_RIGHT),
                 "legacy handing is invalid")
        return module.rea_c10_dimensions(
            _number(config.get("track_gauge")),
            _number(config.get("flangeway")),
        )

    def _legacy_host(self, document, name, set_id):
        module = self.module
        _require(type(name) is str and bool(name), "legacy host name is missing")
        host = document.getObject(name)
        _require(host is not None and host.Document is document
                 and host.Name == name
                 and module.is_turnout_host_centreline(host)
                 and module.object_string_property(host, "GeneratedBy", "")
                 == module.GENERATOR_ID
                 and module.object_string_property(host, "TemplateSetID", "")
                 == set_id, "legacy host ownership is inconsistent")
        return host

    @staticmethod
    def _cached_interval(config, field, interval):
        stored = config.get(field)
        _require(type(stored) is list and len(stored) == 2
                 and tuple(_number(value) for value in stored) == tuple(interval),
                 "legacy cached interval is stale or malformed")

    def _legacy_turnout_interval(self, document, config):
        module = self.module
        dimensions = self._legacy_context(config, "turnout")
        host = self._legacy_host(document, config.get("host_object"),
                                 config["template_set_id"])
        orientation = config.get("orientation")
        _require(orientation in (module.TURNOUT_ORIENTATION_FACING,
                                module.TURNOUT_ORIENTATION_TRAILING),
                 "legacy orientation is invalid")
        _require(type(config.get("turnout_id")) is str
                 and bool(config["turnout_id"])
                 and type(config.get("track_number")) is int
                 and config["track_number"] == module._integer_object_property(
                     host, "TrackNumber", 0,
                 )
                 and config.get("route_id") == module.object_string_property(
                     host, "RouteID", "",
                 ), "legacy turnout host identity is inconsistent")
        toe = _number(config.get("toe_chainage"))
        data = module.turnout_host_alignment(host)
        self._geometry._placement(data, dimensions, toe, config["handing"],
                                   orientation)
        interval = module.turnout_host_station_interval(toe, dimensions,
                                                        orientation)
        self._cached_interval(config, "host_station_interval", interval)
        return host.Name, interval

    def _snapshot(self, document, intent):
        hosts = self._hosts(document, intent)
        source = tuple((obj, value) for obj, value in source_records(document)
                       if value.entity_id != intent.entity_id)
        legacy = self._legacy_records(document)
        # Inherited overlap checks consume cached intervals. Qualify those
        # records before any source geometry can invoke the inherited checks.
        legacy_intervals = tuple(
            interval for kind, _identifier, config, _text in legacy
            for interval in self._legacy_intervals(document, kind, config)
        )
        identifiers = [value.entity_id for _obj, value in source]
        identifiers.extend(identifier for _kind, identifier, _cfg, _text in legacy)
        _require(len(identifiers) == len(set(identifiers))
                 and intent.entity_id not in identifiers,
                 "source and legacy logical identities collide")
        all_hosts = {host.Name: host for host in hosts}
        for _obj, value in source:
            all_hosts.update((host.Name, host) for host in self._hosts(
                document, value,
            ))
        for kind, _identifier, config, _text in legacy:
            names = ((config.get("host_object"),) if kind == "turnout" else
                     (config.get("host_a_object"), config.get("host_b_object")))
            for name in names:
                host = document.getObject(name)
                _require(host is not None and host.Document is document,
                         "legacy occupancy host is missing")
                all_hosts[name] = host
        states = {name: self._host_state(document, host)
                  for name, host in sorted(all_hosts.items())}
        occupancy = _digest({
            "source": [rea_trackwork_intent_to_json(value)
                       for _obj, value in source],
            "legacy": [(kind, identifier, text)
                       for kind, identifier, _config, text in legacy],
            "hosts": states,
        })
        signature = rea_trackwork_geometry_signature(
            intent, host_state=[states[host.Name] for host in hosts],
            occupancy=occupancy,
        )
        return hosts, source, legacy, signature, legacy_intervals

    def _calculate(self, document, intent):
        hosts = self._hosts(document, intent)
        if intent.entity_kind == "turnout":
            return self._geometry.turnout(
                document, hosts[0], intent.reference_chainage_mm,
                intent.handing, intent.orientation, intent.source_specification,
            )
        return self._geometry.crossover(
            document, *hosts, intent.reference_chainage_mm,
            intent.source_specification, arrangement=intent.arrangement,
            handing=intent.handing, minimum_radius=intent.minimum_radius_mm,
        )

    @staticmethod
    def _roads(geometry):
        if "turnout_a" in geometry:
            return (("a", geometry["turnout_a"]),
                    ("b", geometry["turnout_b"]))
        return (("to", geometry),)

    def _legacy_intervals(self, document, kind, config):
        module = self.module
        dimensions = self._legacy_context(config, kind)
        if kind == "turnout":
            return (self._legacy_turnout_interval(document, config),)
        host_a = self._legacy_host(document, config.get("host_a_object"),
                                   config["template_set_id"])
        host_b = self._legacy_host(document, config.get("host_b_object"),
                                   config["template_set_id"])
        _require(host_a is not host_b, "legacy crossover hosts are identical")
        data_a = module.turnout_host_alignment(host_a)
        data_b = module.turnout_host_alignment(host_b)
        reference = _number(config.get("reference_chainage"))
        minimum_radius = _number(config.get("minimum_requested_radius"))
        _require(minimum_radius >= module.CROSSOVER_MINIMUM_ALLOWED_RADIUS,
                 "legacy crossover minimum radius is invalid")
        arrangement = config["arrangement"]
        _require(arrangement in (module.CROSSOVER_ARRANGEMENT_FACING,
                                 module.CROSSOVER_ARRANGEMENT_TRAILING),
                 "legacy crossover arrangement is invalid")
        orientation_a = (module.TURNOUT_ORIENTATION_FACING
                         if arrangement == module.CROSSOVER_ARRANGEMENT_FACING
                         else module.TURNOUT_ORIENTATION_TRAILING)
        self._geometry._placement(data_a, dimensions, reference,
                                   config["handing"], orientation_a)
        orientation_b, _projected, cosine = module._crossover_orientation_b(
            data_a, data_b, reference, orientation_a,
        )
        handing = module._crossover_automatic_hand(
            data_a, data_b, reference, orientation_a,
        )
        _require(config.get("handing") == handing,
                 "legacy crossover handing is stale")
        point_a, _heading = module.interpolate_alignment_station(data_a,
                                                                 reference)
        _station, _point, _heading, separation = (
            module._crossover_nearest_point_on_alignment(data_b, point_a)
        )
        _require(separation <= module.CROSSOVER_MAXIMUM_TRACK_SEPARATION,
                 "legacy crossover separation exceeds the solver limit")
        _require(abs(cosine) >= math.cos(math.radians(30.0)),
                 "legacy crossover hosts are not sufficiently near-parallel")
        solved = module._crossover_solve_toe_b(
            data_a, data_b, reference, orientation_a, orientation_b, handing,
            dimensions, minimum_radius,
        )
        result = []
        radii = []
        for side, host, toe, orientation in (
            ("a", host_a, reference, orientation_a),
            ("b", host_b, solved["toe_b"], orientation_b),
        ):
            child = config.get("turnout_" + side + "_config")
            _require(type(child) is dict, "legacy crossover child is missing")
            child_interval = self._legacy_turnout_interval(document, child)
            _require(_number(config.get("toe_chainage_" + side)) == toe
                     and config.get("orientation_" + side) == orientation
                     and child.get("host_object") == host.Name
                     and _number(child.get("toe_chainage")) == toe
                     and child.get("orientation") == orientation
                     and child.get("handing") == handing
                     and child.get("template_set_id") == config["template_set_id"]
                     and child.get("turnout_id") == config.get(
                         "turnout_" + side + "_id",
                     )
                     and child.get("track_gauge") == config["track_gauge"]
                     and child.get("flangeway") == config["flangeway"],
                     "legacy crossover placement is stale or inconsistent")
            self._cached_interval(config, "host_" + side + "_station_interval",
                                  child_interval[1])
            metrics = module.turnout_mapping_metrics(
                module.turnout_host_alignment(host), toe, orientation,
                handing, dimensions,
            )
            radii.append(metrics["turnout_minimum_radius"])
            result.append(child_interval)
        _require(config["turnout_a_id"] != config["turnout_b_id"],
                 "legacy crossover child identities collide")
        decision = complete_radius_decision(
            *radii, solved["connector"].get("minimum_radius"), minimum_radius,
        )
        _require(decision["accepted"], decision["diagnostic"])
        return tuple(result)

    def _check_occupancy(self, document, geometry, source, legacy_intervals):
        occupied = list(legacy_intervals)
        for _obj, intent in source:
            other = self._calculate(document, intent)
            occupied.extend((road["host_identity"]["object_name"],
                             road["host_station_interval"])
                            for _side, road in self._roads(other))
        for _side, road in self._roads(geometry):
            start, finish = road["host_station_interval"]
            for host_name, (old_start, old_finish) in occupied:
                if host_name != road["host_identity"]["object_name"]:
                    continue
                overlap = min(finish, old_finish) - max(start, old_start)
                _require(overlap <= self.module.TURNOUT_OVERLAP_TOLERANCE,
                         "source or legacy occupancy overlap")

    def _scene(self, intent, geometry):
        lines = []
        for side, road in self._roads(geometry):
            for rail in road["rails"]:
                lines.append((intent.entity_id + ":" + side + ":rail:"
                              + rail["name"], "rails",
                              tuple(_point(p) for p in rail["points"])))
            for timber in road["timbers"]:
                lines.append((intent.entity_id + ":" + side + ":timber:"
                              + timber["identifier"], "timbers",
                              tuple(_point(p) for p in timber["points"])))
        if "connector" in geometry:
            dimensions = geometry["turnout_a"]["dimensions"]
            gauge, width = dimensions["gauge"], dimensions["rail_head_width"]
            for name, offset in (("left-gauge", gauge / 2),
                                 ("left-outer", gauge / 2 + width),
                                 ("right-gauge", -gauge / 2),
                                 ("right-outer", -gauge / 2 - width)):
                points = self.module._crossover_offset_polyline(
                    geometry["connector"]["points"], offset,
                )
                lines.append((intent.entity_id + ":connector:" + name,
                              "rails", tuple(_point(p) for p in points)))
        return self.scene_factory(intent.entity_id, tuple(lines))

    def prepare(self, document, intent, *, existing=None):
        """Prepare complete current data without changing a document."""
        _require(type(intent) is ReaTrackworkIntent,
                 "an explicit source intent is required")
        rea_trackwork_intent_to_json(intent)
        previous_payload = None
        if existing is not None:
            previous = next((value for obj, value in source_records(document)
                             if obj is existing), None)
            _require(previous is not None
                     and previous.entity_id == intent.entity_id,
                     "the edited logical object is missing or changed")
            previous_payload = getattr(existing, REA_INTENT_JSON_PROPERTY)
        hosts, source, _legacy, signature, intervals = self._snapshot(
            document, intent,
        )
        geometry = self._calculate(document, intent)
        self._check_occupancy(document, geometry, source, intervals)
        scene = self._scene(intent, geometry)
        _require(signature == self._snapshot(document, intent)[3],
                 "inputs changed during preparation")
        settings = self.module.settings_for_template_set(
            document, intent.template_set_id,
        )
        prepared = _PreparedTrackwork(
            self._owner, document, intent, hosts, scene, signature, existing,
            previous_payload, hosts + (settings,),
        )
        self._prepared = prepared
        return prepared

    def commit(self, document, prepared):
        """Commit only this coordinator's current preparation."""
        _require(type(prepared) is _PreparedTrackwork
                 and prepared is self._prepared
                 and prepared.owner is self._owner
                 and prepared.document is document,
                 "foreign or malformed preparation")
        self._prepared = None
        if prepared.existing is not None:
            _require(getattr(prepared.existing, REA_INTENT_JSON_PROPERTY)
                     == prepared.previous_payload,
                     "the edited intent changed after preparation")
        current = lambda: self._snapshot(document, prepared.intent)[3]
        _require(current() == prepared.signature,
                 "inputs changed after preparation")
        arguments = dict(hosts=prepared.hosts, current_signature=current,
                         dependencies=prepared.dependencies)
        if prepared.existing is None:
            return self.store.create(
                document, prepared.intent, prepared.scene, prepared.signature,
                **arguments,
            )
        return self.store.update(
            document, prepared.existing, prepared.intent, prepared.scene,
            prepared.signature, **arguments,
        )

    def create(self, document, intent):
        return self.commit(document, self.prepare(document, intent))

    def update(self, document, obj, intent):
        return self.commit(document, self.prepare(document, intent,
                                                  existing=obj))

    def rebuild(self, document, obj):
        """Recreate a current derived view after open or invalidation."""
        intent = next((value for candidate, value in source_records(document)
                       if candidate is obj), None)
        _require(intent is not None, "logical source object is missing")
        prepared = self.prepare(document, intent, existing=obj)
        self._prepared = None
        return self.store.rebuild(
            obj, prepared.scene, prepared.signature,
            current_signature=lambda: self._snapshot(document, intent)[3],
            dependencies=prepared.dependencies,
        )
