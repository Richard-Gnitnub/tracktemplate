#!/usr/bin/env python3
"""Check canonical dependency orchestration without a FreeCAD runtime.

The legacy witness executes the actual frozen removal function on a small
document. It proves canonical deletion, not native transaction recovery or
railway geometry. Qualified native and GUI proofs own those boundaries.
"""

import argparse
import ast
import copy
import json
import math
from pathlib import Path
import sys
from types import ModuleType
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
LEGACY = ROOT / (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)
SENTINEL = "Phase 9B P dependent recalculation standalone validation passed"
INTEGRATION_ROLES = {
    "CROSSOVER_INTEGRATION_GROUP_ROLE": "CrossoverHostIntegrationGroup",
    "CROSSOVER_INTEGRATION_SETTINGS_ROLE": "CrossoverHostIntegrationSettings",
    "CROSSOVER_INTEGRATED_DISPLAY_ROLE": "CrossoverIntegratedHostDisplay",
    "CROSSOVER_INTEGRATED_TEMPLATE_ROLE": "CrossoverIntegratedHostTemplate",
    "CROSSOVER_INTEGRATED_OUTLINE_ROLE": "CrossoverIntegratedHostOutline",
    "CROSSOVER_INTEGRATED_TIMBER_ROLE": "CrossoverIntegratedResolvedTimberGeometry",
}
EXTENSION_METADATA = (
    "extended_from_turnout_id", "extension_preserved_toe_chainage",
    "extension_preserved_handing", "extension_preserved_orientation",
    "extension_mode", "conversion_source_turnout_config",
)


def _copy(value):
    return copy.deepcopy(value)


class _Object:
    """Minimal native property witness for the unchanged removal code."""

    def __init__(self, name, role, *, generated=True):
        self.Name = name
        self.GeneratedBy = "TrackTemplate" if generated else ""
        self.GeneratedRole = role
        self.TemplateSetID = "SET-001" if generated else ""
        self.Visibility = True

    @property
    def PropertiesList(self):
        return list(vars(self))


class _Document:
    """Preserve observable state at an explicit fake transaction boundary."""

    def __init__(self):
        self.Name = "DependentRecalculationWitness"
        self.Objects = [
            _Object("RailwayTrackCentreline_00", "Centreline"),
            _Object("RailwayTrackCentreline_01", "Centreline"),
            _Object("CrossoverSettings", "CrossoverSettings"),
            _Object("ForeignWitness", "Unrelated", generated=False),
        ]
        self.Objects[2].CrossoverID = "XO-001"
        self.UndoMode = 1
        self.UndoCount = 0
        self.RedoCount = 0
        self.pending = None
        self.recomputes = 0

    def getObject(self, name):
        return next((obj for obj in self.Objects if obj.Name == name), None)

    def removeObject(self, name):
        self.Objects = [obj for obj in self.Objects if obj.Name != name]

    def openTransaction(self, _label):
        assert self.pending is None, "Unexpected nested native transaction"
        self.pending = copy.deepcopy(self.Objects)

    def commitTransaction(self):
        assert self.pending is not None, "Commit without outer transaction"
        self.pending = None
        self.UndoCount += 1
        self.RedoCount = 0

    def abortTransaction(self):
        assert self.pending is not None, "Abort without outer transaction"
        self.Objects = self.pending
        self.pending = None


def _legacy_module():
    """Execute the frozen deletion code rather than imitate its outcome."""
    module = ModuleType("_dependent_legacy_witness")
    module.GENERATOR_ID = "TrackTemplate"
    module.GROUP_NAME = "RailwayGroup"
    module.object_string_property = (
        lambda obj, name, default="": str(getattr(obj, name, default))
    )
    module.is_generated_template = lambda _obj: False
    module.is_generated_centreline = lambda _obj: False

    exec("def _document_recompute(document):\n"
         "    document.recomputes += 1\n", module.__dict__)
    tree = ast.parse(LEGACY.read_text(encoding="utf-8"))
    names = {
        "is_any_generated_output", "is_generated_group",
        "remove_all_generated_outputs",
    }
    functions = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in functions} == names
    extracted = ast.Module(body=functions, type_ignores=[])
    exec(compile(extracted, str(LEGACY), "exec"), module.__dict__)
    return module


def legacy_deletion_witness():
    """Require the new outcome from the unchanged destructive boundary."""
    module = _legacy_module()
    document = _Document()
    original = document.getObject("CrossoverSettings")
    foreign = document.getObject("ForeignWitness")
    document.openTransaction("Generate curve and straight templates")
    module.remove_all_generated_outputs(document)
    document.commitTransaction()
    assert document.getObject("ForeignWitness") is foreign
    current = document.getObject("CrossoverSettings")
    assert current is not None and current.CrossoverID == original.CrossoverID, (
        "Canonical XO-001 dependency was deleted by inherited Replace; "
        "automatic dependent recalculation did not occur"
    )


_GENERATE = '''
def run_macro():
    doc = App.ActiveDocument
    if cancelled:
        return
    values = dict(request)
    remember_last_dialog_inputs(doc, **values)
    if replace_cancelled:
        return
    validate_production_export_request(values['production_export_config'], {})
    doc.openTransaction('Generate curve and straight production templates')
    try:
        if values['output_mode'] == OUTPUT_REPLACE:
            remove_all_generated_outputs(doc)
        make_replacement_hosts(doc, values)
        store_parameters(latest_generated_settings(doc), values['transition'],
                         values['radius'], values['angle'], values['main_width'],
                         values['track_configs'])
        settings_object = latest_generated_settings(doc)
        set_id = 'SET-001'
        production_record_index = read_production_record_index(settings_object)
        _document_recompute(doc)
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        raise
    try:
        production_schedule_rows = build_production_schedule_rows(
            production_record_index, values['production_export_config'], set_id)
        sheet = create_or_replace_production_schedule(
            doc, set_id, production_schedule_rows)
        report_returns.append(('schedule', sheet))
    except Exception as error:
        report_errors.append(('schedule', str(error)))
    try:
        material_report_config = read_material_report_config(settings_object)
        material_report_rows, material_report_diagnostics = build_material_report_rows(
            doc, production_record_index, settings_object, material_report_config, set_id)
        sheet = create_or_replace_material_report(
            doc, set_id, material_report_rows, material_report_config,
            material_report_diagnostics)
        report_returns.append(('material', sheet))
    except Exception as error:
        report_errors.append(('material', str(error)))
    _document_recompute(doc)
'''


def _request(radius=600.0):
    """Only radius changes in the admitted fake canonical request."""
    return {
        "transition": 600.0, "radius": radius, "angle": 90.0,
        "main_width": 32.0, "track_configs": [{
            "name": "Track 2", "side": "Outside",
            "alignment_mode": "Euler - match spacings",
            "start_spacing": 50.0, "curve_spacing": 55.0,
            "finish_spacing": 50.0, "width": 32.0,
            "entry_transition_length": 559.4102547270278,
            "exit_transition_length": 559.4102547270278,
            "create_template": True, "show_centreline": True,
        }],
        "straight_configs": [], "selected_straight_index": 0,
        "platform_configs": [], "selected_platform_id": "",
        "selected_platform_index": 0, "formation_config": {"enabled": False},
        "section_config": {"enabled": False},
        "registration_config": {"enabled": False},
        "template_assembly_config": {"enabled": False},
        "production_export_config": {"enabled": False},
        "output_mode": "Replace existing",
    }


def _config():
    """Synthetic current dependency; no claim of physical railway geometry."""
    from tracktemplate.compatibility.chair_catalogue_placement import (
        _CODE75_PROFILE,
    )

    result = {
        "crossover_id": "XO-001", "schema_version": 1,
        "template_set_id": "SET-001", "size": "C10",
        "host_a_object": "RailwayTrackCentreline_00",
        "host_b_object": "RailwayTrackCentreline_01",
        "turnout_a_id": "XO-001-A001", "turnout_b_id": "XO-001-B001",
        "reference_chainage": 746.298, "toe_chainage_a": 746.298,
        "toe_chainage_b": 1590.0, "arrangement": "Facing crossover",
        "handing": "Right-hand", "track_gauge": 16.5, "flangeway": 1.0,
        "template_thickness": 1.0, "minimum_requested_radius": 600.0,
        "minimum_resulting_radius": 676.0, "integration_active": False,
        "integration_result": {}, "edit_revision": 0,
        "timber_analysis_settings": {"fixture": "timber"},
        "shared_timber_settings": {"fixture": "shared"},
        "b3_settings": {"fixture": "b3"},
        "b4_settings": {"fixture": "b4"},
        "chair_analysis_settings": {
            "rail_profile_id": dict(_CODE75_PROFILE)["profile_id"],
            "future_chair_embed_depth": 0.2, "cache_enabled": True,
        },
        "production_ready": False,
    }
    for side in ("a", "b"):
        result["turnout_" + side + "_config"] = {
            "turnout_id": result["turnout_" + side + "_id"],
            "host_object": result["host_" + side + "_object"],
            "size": "C10", "track_gauge": 16.5, "flangeway": 1.0,
            "template_thickness": 1.0, "template_set_id": "SET-001",
        }
    return result


class _FixtureDocument(_Document):
    """Transactional protocol fake; native proof owns real FreeCAD behavior."""

    def __init__(self):
        super().__init__()
        self.config = _config()
        self.radius = 600.0
        self.analysis = None
        self.records = [
            {"record_id": "host/current", "source_name": "HostTemplate",
             "source_radius": self.radius, "template_set_id": "SET-001"},
            {"record_id": "XO-001/current", "source_name": "CrossoverTemplate",
             "source_radius": self.radius, "template_set_id": "SET-001"},
        ]
        self.history = []
        self.future = []
        self.add_settings()
        self.Objects.extend((
            _Object("HostTemplate", "Template"),
            _Object("CrossoverTemplate", "CrossoverTemplate"),
        ))
        for number in range(2):
            host = self.getObject("RailwayTrackCentreline_0" + str(number))
            self.host_metadata(host, number)

    @staticmethod
    def host_metadata(host, number, *, route_metadata=False):
        host.GeneratedRole = "Centreline"
        host.TrackNumber = number + 1
        host.TrackName = ("Main Track", "Track 2")[number]
        host.ExportSubtype = "TrackCentreline"
        if route_metadata:
            host.RouteID = "route-" + str(number)
            host.RouteName = "Route " + str(number)

    def add_settings(self):
        settings = _Object("Settings", "Settings")
        settings.TransitionLength = 600.0
        settings.CurveRadius = self.radius
        settings.TotalTurnAngle = 90.0
        settings.MainTemplateWidth = 32.0
        settings.TemplateWidth = 32.0
        settings.inputs = _request(self.radius)
        settings.Document = self
        self.Objects.append(settings)

    def state(self):
        return _copy({
            "objects": [{key: value for key, value in vars(obj).items()
                         if key != "Document"} for obj in self.Objects],
            "config": self.config, "radius": self.radius,
            "analysis": self.analysis, "records": self.records,
        })

    def _restore(self, state):
        self.Objects = []
        for item in state["objects"]:
            obj = _Object.__new__(_Object)
            obj.__dict__.update(_copy(item))
            self.Objects.append(obj)
        for obj in self.Objects:
            obj.Document = self
        for key in ("config", "radius", "analysis", "records"):
            setattr(self, key, _copy(state[key]))

    def removeObject(self, name):
        super().removeObject(name)
        if name == "CrossoverSettings":
            self.config = None
            self.analysis = None

    def openTransaction(self, _label):
        assert self.pending is None, "Unexpected nested native transaction"
        self.pending = self.state()

    def commitTransaction(self):
        assert self.pending is not None, "Commit without outer transaction"
        self.history.append(self.pending)
        self.pending = None
        self.future = []
        self.UndoCount = len(self.history)
        self.RedoCount = 0

    def abortTransaction(self):
        assert self.pending is not None, "Abort without outer transaction"
        self._restore(self.pending)
        self.pending = None

    def undo(self):
        self.future.append(self.state())
        self._restore(self.history.pop())
        self.UndoCount, self.RedoCount = len(self.history), len(self.future)

    def redo(self):
        self.history.append(self.state())
        self._restore(self.future.pop())
        self.UndoCount, self.RedoCount = len(self.history), len(self.future)

    def set_analysis(self, result):
        self.analysis = result

    def set_records(self, records):
        self.records = records


class _Fixture:
    """Expose host protocols while retaining independent expected outcomes."""

    def __init__(self, *, integrated=False, route_metadata=False):
        self.doc = _FixtureDocument()
        self.module = _legacy_module()
        self.fault = None
        self.calls = []
        self.wrong_host = False
        self.stale_analysis = False
        self.wrong_rebuilt_ids = False
        self.reenter = False
        self.route_metadata = route_metadata
        self.host_change = None
        self.extra_crossovers = []
        self.extra_turnouts = []
        self.broken_hydration = False
        self.stale_rebuilt_integration = False
        self.report_inputs = []
        self.evaluated_tracks = None
        self.stored_track_change = None
        self.evaluated_store_inputs = []
        for number in range(2):
            host = self.doc.getObject("RailwayTrackCentreline_0" + str(number))
            self.doc.host_metadata(host, number, route_metadata=route_metadata)
        self._install()
        self._b4(self.doc, "XO-001")
        if integrated:
            self.module.create_crossover_host_integration(self.doc, "XO-001")
        self._analyse(self.doc, "crossover", "XO-001")
        self.doc.history.clear()
        self.doc.UndoCount = 0
        self.calls.clear()

    def _fault(self, stage):
        self.calls.append(stage)
        if self.fault == stage:
            raise RuntimeError("Injected " + stage + " failure")

    def _install(self):
        module = self.module
        module.App = SimpleNamespace(ActiveDocument=self.doc)
        module.OUTPUT_REPLACE = "Replace existing"
        module.OUTPUT_CREATE_NEW = "Create new"
        module.TURNOUT_SIZE_C10 = "C10"
        module.TURNOUT_DEFAULT_SCALE = 76.2
        module.CROSSOVER_SCHEMA_VERSION = 1
        module.CROSSOVER_ID_PROPERTY = "CrossoverID"
        module.CROSSOVER_SETTINGS_ROLE = "CrossoverSettings"
        module.TURNOUT_SETTINGS_ROLE = "TurnoutSettings"
        module.TURNOUT_ID_PROPERTY = "TurnoutID"
        module.CROSSOVER_REVERSION_SIDE_A = "A"
        module.CROSSOVER_REVERSION_SIDE_B = "B"
        module.CROSSOVER_INTEGRATION_SCHEMA_VERSION = 1
        module.CROSSOVER_INTEGRATION_PROPERTY = "CrossoverHostIntegrationJSON"
        module.CROSSOVER_INTEGRATION_STATUS_ACTIVE = (
            "Integrated with host templates — chair validation outstanding"
        )
        for name, value in INTEGRATION_ROLES.items():
            setattr(module, name, value)
        module.MACRO_VERSION_NUMBER = "B16"
        module.MODE_MATCH_SPACINGS = "Euler - match spacings"
        module.MODE_USE_LENGTHS = "Euler - use lengths"
        module.MODE_PLATFORM = "Platform widening"
        module.PRODUCTION_SCHEDULE_ROLE = "ProductionSchedule"
        module.MATERIAL_REPORT_ROLE = "MaterialLengthReport"
        module.CHAIR_ASSIGNMENT_CONFIRMED = "confirmed"
        module.CHAIR_FAMILY_SLIDE = "slide chair"
        module.CHAIR_CLASS_SOURCE = "source"
        module.cancelled = False
        module.replace_cancelled = False
        module.request = _request()
        module.report_errors = []
        module.report_returns = []
        module.read_material_report_config = lambda _obj: {
            "fixture": "material settings",
        }
        module.latest_generated_settings = lambda doc: doc.getObject("Settings")
        module.settings_for_template_set = lambda doc, _identifier: (
            doc.getObject("Settings")
        )
        module.read_production_record_index = lambda settings: {
            "schema_version": 2, "records": _copy(settings.Document.records),
        }
        module.quantity_value = (
            lambda obj, name, default: getattr(obj, name, default)
        )
        module._integer_object_property = (
            lambda obj, name, default: int(getattr(obj, name, default))
        )
        module.is_turnout_host_centreline = (
            lambda obj: obj is not None
            and obj.GeneratedRole == "Centreline"
            and obj.ExportSubtype == "TrackCentreline"
        )
        module.existing_crossover_configs = lambda doc: (
            ([doc.config] if doc.config else []) + self.extra_crossovers
        )
        module.existing_turnout_configs = lambda _doc: self.extra_turnouts
        module.crossover_config_by_id = (
            lambda doc, identifier: doc.config if doc.config
            and doc.config["crossover_id"] == identifier else None
        )
        module._crossover_integration_objects = self._integration_objects
        module.crossover_host_integration_by_id = self._integration_by_id
        module.crossover_host_integration_effective_status = (
            self._integration_status
        )
        module._crossover_integration_restored_records = self._restored_records
        for name in (
            "track", "straight", "platform", "formation", "section",
            "registration", "template_assembly", "production_export",
        ):
            plural = name in ("track", "straight", "platform")
            key = name + ("_configs" if plural else "_config")
            setattr(module, "read_" + key,
                    lambda obj, *_args, key=key: _copy(obj.inputs[key]))
        module._remember = self._remember
        module._validate = self._validate
        module._store = self._store
        module._integrate = self._integrate
        module._build_schedule = self._build_schedule
        module._build_material = self._build_material
        module._write_report = self._write_report
        exec('''
def remember_last_dialog_inputs(doc, transition, radius, angle, main_width,
        track_configs, straight_configs, selected_straight_index,
        platform_configs, selected_platform_id, selected_platform_index,
        formation_config, section_config, registration_config,
        template_assembly_config, production_export_config, output_mode):
    _remember(doc, radius)

def validate_production_export_request(config, capabilities):
    return _validate(config, capabilities)

def store_parameters(obj, transition, radius, angle, main_width, track_configs):
    return _store(obj, transition, radius, angle, main_width, track_configs)

def create_crossover_host_integration(doc, identifier):
    return _integrate(doc, identifier)

def remove_crossover_host_integration(doc, identifier):
    raise AssertionError('Automatic regeneration must not invoke Remove')

def build_production_schedule_rows(index_payload, export_config, set_id):
    return _build_schedule(index_payload, export_config, set_id)

def create_or_replace_production_schedule(doc, set_id, rows):
    return _write_report(doc, set_id, rows, 'schedule')

def build_material_report_rows(doc, index_payload, settings, config, set_id):
    return _build_material(doc, index_payload, settings, config, set_id)

def create_or_replace_material_report(doc, set_id, rows, config, diagnostics=None):
    return _write_report(doc, set_id, rows, 'material', config, diagnostics)
''', module.__dict__)
        from tracktemplate.compatibility.crossover_host_integration_recovery import (
            CrossoverHostIntegrationRecoveryAdapter,
        )

        recovery = CrossoverHostIntegrationRecoveryAdapter(
            module, module.create_crossover_host_integration,
            module.remove_crossover_host_integration,
        )
        module.create_crossover_host_integration = recovery.create
        module.remove_crossover_host_integration = recovery.remove
        module.make_replacement_hosts = self._replace_hosts
        module._build_rea_c10_crossover_geometry = self._build
        module._commit_rea_c10_crossover_objects = self._commit
        module._turnout_store_production_records = self._records
        module._crossover_store_catalogue = self._catalogue
        module.apply_crossover_b4_timbering = self._b4
        module.analyse_entity_chair_positions = self._analyse
        module._chair_generation_context = self._context
        module._A8A7B15_BUILD_SOLID_PLAN = self._plan
        module.crossover_inherited_timber_records = lambda doc, _cfg: (
            [{"source_radius": doc.radius}]
        )
        module._crossover_b4_result_is_current = (
            lambda _cfg, inherited, result: result.get("resolved_timbers")
            == inherited
        )
        exec(_GENERATE, module.__dict__)

    def _remember(self, _doc, radius):
        # Dialog memory is deliberately outside canonical document state.
        self.remembered_radius = radius

    def _validate(self, _config, _capabilities):
        self._fault("input validation")

    def _store(self, obj, transition, radius, angle, width, track_configs):
        obj.TransitionLength, obj.CurveRadius = transition, radius
        obj.TotalTurnAngle, obj.MainTemplateWidth = angle, width
        self.evaluated_store_inputs.append(_copy(track_configs))
        obj.inputs["track_configs"] = _copy(track_configs)
        if self.stored_track_change is not None:
            self.stored_track_change(obj.inputs["track_configs"])
        self._fault("settings stored")

    def _replace_hosts(self, doc, values):
        self._fault("host replacement")
        if self.evaluated_tracks is not None:
            values["track_configs"] = _copy(self.evaluated_tracks)
        if values["output_mode"] == self.module.OUTPUT_CREATE_NEW:
            return
        doc.radius = values["radius"]
        for number in range(2):
            host = _Object("RailwayTrackCentreline_0" + str(number), "")
            doc.host_metadata(host, number, route_metadata=self.route_metadata)
            if self.wrong_host and number == 1:
                host.RouteID = "wrong route despite same name"
            if self.host_change is not None and number == 1:
                self.host_change(host)
            doc.Objects.append(host)
        doc.Objects.append(_Object("HostTemplate", "Template"))
        doc.set_records([{
            "record_id": "host/current", "source_name": "HostTemplate",
            "source_radius": doc.radius, "template_set_id": "SET-001",
        }])
        doc.add_settings()

    def _build(self, doc, host_a, host_b, chainage, arrangement, handing,
               gauge, flangeway, minimum, **keywords):
        self._fault("crossover build")
        if self.reenter:
            self.module.run_macro()
        assert keywords["crossover_id"] == "XO-001"
        assert keywords["turnout_a_id_override"] == "XO-001-A001"
        assert doc.pending is not None
        if not math.isfinite(doc.radius) or doc.radius <= 0:
            raise ValueError("Invalid radius")
        result = _config()
        result.update(
            host_a_object=host_a.Name, host_b_object=host_b.Name,
            reference_chainage=chainage, toe_chainage_a=chainage,
            toe_chainage_b=doc.radius + 990.0, arrangement=arrangement,
            handing=handing, track_gauge=gauge, flangeway=flangeway,
            minimum_requested_radius=minimum,
        )
        return {"config": result, "set_id": "SET-001", "opaque": object()}

    def _commit(self, doc, built):
        assert doc.pending is not None
        doc.config = _copy(built["config"])
        obj = _Object("CrossoverSettings", "CrossoverSettings")
        obj.CrossoverID = doc.config["crossover_id"]
        doc.Objects.append(obj)
        doc.Objects.append(_Object("CrossoverTemplate", "CrossoverTemplate"))
        self._fault("crossover committed")
        return {"records": [{
            "record_id": "XO-001/current", "source_name": "CrossoverTemplate",
            "source_radius": doc.radius, "template_set_id": "SET-001",
        }]}

    def _records(self, doc, _set_id, records, **_kwargs):
        doc.records.extend(_copy(records))

    def _catalogue(self, _doc, _set_id):
        self._fault("catalogue written")

    def _build_schedule(self, index_payload, _export_config, set_id):
        self._fault("schedule rows built")
        assert set_id == "SET-001"
        rows = _copy(index_payload["records"])
        self.report_inputs.append(("schedule", rows,
                                   self.module.App.ActiveDocument.pending is not None))
        return rows

    def _build_material(self, doc, index_payload, settings, config, set_id):
        self._fault("material rows built")
        assert set_id == "SET-001" and settings.Document.Name == doc.Name
        assert config == {"fixture": "material settings"}
        rows = _copy(index_payload["records"])
        self.report_inputs.append(("material", rows, doc.pending is not None))
        return rows, {"physical_part_count": len(rows)}

    def _write_report(self, doc, set_id, rows, kind, config=None, diagnostics=None):
        """Use inherited report transaction order and opaque row contents."""
        assert set_id == "SET-001"
        doc.openTransaction("Update Version B16 " + (
            "production schedule" if kind == "schedule" else "material report"))
        try:
            name = "ProductionSchedule" if kind == "schedule" else "MaterialReport"
            if doc.getObject(name) is not None:
                doc.removeObject(name)
            role = "ProductionSchedule" if kind == "schedule" else "MaterialLengthReport"
            sheet = _Object(name, role)
            sheet.Rows = _copy(rows)
            sheet.ReportConfig = _copy(config)
            sheet.ReportDiagnostics = _copy(diagnostics)
            doc.Objects.append(sheet)
            self._fault(kind + " written")
            self.module._document_recompute(doc)
            doc.commitTransaction()
            return sheet
        except Exception:
            doc.abortTransaction()
            raise

    def _b4(self, doc, _identifier, *_args, **_kwargs):
        nested = doc.pending is not None
        if nested:
            doc.openTransaction("Apply Version B16 hybrid timbering XO-001")
        doc.config["b4_result"] = {
            "applied": True, "resolved_timbers": [{"source_radius": doc.radius}],
            "resolution_signature": "b4:" + str(doc.radius),
        }
        self._fault("b4 written")
        self.module._document_recompute(doc)
        if nested:
            doc.commitTransaction()
        return {**doc.config["b4_result"], "cache_reused": False}

    @staticmethod
    def _integration_objects(doc, identifier):
        return [obj for obj in doc.Objects
                if getattr(obj, "CrossoverID", "") == identifier
                and obj.GeneratedRole in INTEGRATION_ROLES.values()]

    def _integration_by_id(self, doc, identifier):
        for obj in self._integration_objects(doc, identifier):
            if obj.GeneratedRole == "CrossoverHostIntegrationSettings":
                try:
                    value = json.loads(obj.CrossoverHostIntegrationJSON)
                except (AttributeError, ValueError):
                    return None
                return value if isinstance(value, dict) else None
        return None

    def _integration_status(self, doc, config):
        record = self._integration_by_id(doc, "XO-001")
        expected = "integration:" + str(doc.radius)
        if (not config.get("integration_active") or not record
                or config.get("integration_signature") != expected
                or record.get("signature") != expected
                or not all(doc.getObject(name) is not None
                           for name in record.get("integration_object_names", []))):
            return "Host integration stale"
        return self.module.CROSSOVER_INTEGRATION_STATUS_ACTIVE

    def _restored_records(self, doc, record, **_kwargs):
        metadata = (record["original_host_record_metadata"]
                    + record["original_crossover_record_metadata"])
        return [{**item, "shape": None if self.broken_hydration or
                 doc.getObject(item["source_name"]) is None else
                 "hydrated:" + item["source_name"]} for item in metadata]

    def _integrate(self, doc, identifier):
        """Model writes through the actual accepted recovery transaction facade."""
        assert identifier == "XO-001"
        assert doc.config["b4_result"]["resolved_timbers"] == [
            {"source_radius": doc.radius},
        ], "Integration consumed stale B4"
        # Existing integration clears chair state before its inner transaction.
        doc.set_analysis(None)
        doc.openTransaction("Integrate Version B16 crossover XO-001 with host templates")
        names = []
        for index, role in enumerate(INTEGRATION_ROLES.values()):
            obj = _Object("Integration" + str(index), role)
            obj.CrossoverID = identifier
            obj.Shape = "integration-shape:" + str(doc.radius)
            obj.Visibility = role in {
                "CrossoverIntegratedHostDisplay",
                "CrossoverIntegratedResolvedTimberGeometry",
            }
            doc.Objects.append(obj)
            names.append(obj.Name)
        status = self.module.CROSSOVER_INTEGRATION_STATUS_ACTIVE
        record = {
            "schema_version": 1, "crossover_id": identifier,
            "template_set_id": "SET-001", "status": status,
            "signature": "integration:" + str(doc.radius),
            "b4_signature": doc.config["b4_result"]["resolution_signature"],
            "sectioned": False, "section_number": 0,
            "integration_object_names": names,
            "source_visibility": {"HostTemplate": True},
            "crossover_visibility": {"CrossoverTemplate": True},
            "source_record_ids": [item["record_id"] for item in doc.records],
            "original_host_record_metadata": [
                _copy(item) for item in doc.records
                if item["source_name"] == "HostTemplate"],
            "original_crossover_record_metadata": [
                _copy(item) for item in doc.records
                if item["source_name"] == "CrossoverTemplate"],
        }
        if self.stale_rebuilt_integration:
            record["signature"] = "previous-host-integration"
        doc.config.update(
            integration_active=True, integration_schema_version=1,
            integration_status=status, integration_signature=record["signature"],
            integration_result=_copy(record), host_integration_allowed=True,
            production_ready=False,
        )
        for obj in self._integration_objects(doc, identifier):
            obj.CrossoverHostIntegrationJSON = json.dumps(record, sort_keys=True)
        doc.set_records([
            {"record_id": "integrated/" + str(index), "source_name": name,
             "source_radius": doc.radius, "template_set_id": "SET-001"}
            for index, name in enumerate(names[3:])
        ])
        for item in doc.records:
            doc.getObject(item["source_name"]).ProductionRecordIDsJSON = (
                json.dumps([item["record_id"]])
            )
        self._fault("integration records written")
        for name in ("HostTemplate", "CrossoverTemplate"):
            doc.getObject(name).Visibility = False
        self._fault("integration visibility written")
        self.module._document_recompute(doc)
        doc.commitTransaction()
        return _copy(doc.config)

    def _analyse(self, doc, _kind, _identifier, settings=None):
        nested = doc.pending is not None
        if nested:
            doc.openTransaction("Analyse crossover chair positions XO-001")
        if not self.stale_analysis:
            doc.set_analysis({
                "geometry_signature": "radius:" + str(doc.radius),
                "positions": [
                    {"stable_chair_position_identity": f"P-{side}-{index}",
                     "chair_code": 2, "chair_code_label": "P",
                     "assignment_status": "confirmed",
                     "parent_turnout_identity": f"XO-001-{side}001",
                     "centre_point": [doc.radius, float(index)]}
                    for side in ("A", "B") for index in range(14)
                ],
                "cache_reused": False,
            })
            if self.wrong_rebuilt_ids:
                doc.analysis["positions"][0][
                    "stable_chair_position_identity"
                ] = "unexpected-new-chair-identity"
        doc.config["chair_analysis_signature"] = (
            doc.analysis["geometry_signature"] if doc.analysis else "stale"
        )
        self._fault("analysis written")
        self.module._document_recompute(doc)
        if nested:
            doc.commitTransaction()
        return _copy(doc.analysis)

    def _context(self, doc, kind, identifier, *_args):
        assert kind == "crossover" and identifier == "XO-001"
        if not doc.analysis or doc.analysis["geometry_signature"] != (
            "radius:" + str(doc.radius)
        ):
            raise ValueError("Chair analysis is stale")
        return (kind, _copy(doc.config), _copy(doc.analysis),
                _copy(doc.config["chair_analysis_settings"]), [],
                [{"source_radius": doc.radius}])

    @staticmethod
    def _plan(_doc, _kind, _config, _analysis, _rails, _timbers, settings):
        from tracktemplate.compatibility.chair_catalogue_placement import (
            _CODE75_PROFILE,
        )

        return {
            "entity_kind": "crossover", "entity_id": "XO-001",
            "rail_profile": dict(_CODE75_PROFILE),
            "settings": {"embed_depth": settings["future_chair_embed_depth"]},
        }

    @staticmethod
    def select_protocol_positions(_module, analysis, *_args, **_kwargs):
        """Stand in for qualified frame math, not an alternative oracle.

        Native proofs retain the real selector and independent raw-source
        frame oracle. This unit layer checks orchestration of its result.
        """
        placements = tuple(SimpleNamespace(
            position_id=item["stable_chair_position_identity"],
        ) for item in analysis["positions"]
            if item["chair_code"] == 2
            and item["assignment_status"] == "confirmed")
        return placements, [], [], 0.8


_HOOKS = (
    "remember_last_dialog_inputs", "validate_production_export_request",
    "remove_all_generated_outputs", "store_parameters", "_document_recompute",
    "build_production_schedule_rows", "create_or_replace_production_schedule",
    "build_material_report_rows", "create_or_replace_material_report",
)


def _install_adapter(fixture):
    from tracktemplate.compatibility.crossover_dependent_recalculation import (
        CrossoverDependentRecalculationAdapter,
    )

    module = fixture.module
    original = module.run_macro
    adapter = CrossoverDependentRecalculationAdapter(module, original)
    module.__dict__.update(adapter.bindings)
    assert module.run_macro is original
    return adapter


def _run(fixture, radius):
    """Call the normal command with exact chair construction forbidden."""
    from tracktemplate.application import chair_catalogue
    from tracktemplate.compatibility import chair_catalogue_placement
    from tracktemplate.compatibility import crossover_dependent_recalculation

    module = fixture.module
    module.request["radius"] = radius
    hooks = {name: getattr(module, name) for name in _HOOKS}
    try:
        with (
            patch.object(chair_catalogue_placement, "prepare_catalogue_chair",
                         side_effect=AssertionError("Eager exact chair")),
            patch.object(chair_catalogue, "prepare_catalogue_chair",
                         side_effect=AssertionError("Eager chair catalogue")),
            patch.dict(sys.modules, {"Part": None, "FreeCAD": None}),
            patch.object(crossover_dependent_recalculation,
                         "_select_p_positions",
                         fixture.select_protocol_positions),
        ):
            module.run_macro()
    finally:
        assert all(getattr(module, name) is hook
                   for name, hook in hooks.items()), "Scoped hook leaked"


def _identities(analysis):
    return tuple(sorted(item["stable_chair_position_identity"]
                        for item in analysis["positions"]))


def _expect_rejection(action, text=None):
    try:
        action()
    except (ValueError, RuntimeError) as error:
        if text is not None:
            assert text in str(error), str(error)
        return str(error)
    raise AssertionError("Invalid dependency was accepted")


def validate_curved_host_without_route():
    """Native generated curved hosts have no RouteID or RouteName property."""
    fixture = _Fixture(integrated=True)
    _install_adapter(fixture)
    original_ids = _identities(fixture.doc.analysis)
    for radius in (900.0, 600.0):
        _run(fixture, radius)
        for number in range(2):
            host = fixture.doc.getObject("RailwayTrackCentreline_0" + str(number))
            assert host.GeneratedRole == "Centreline"
            assert host.ExportSubtype == "TrackCentreline"
            assert host.TrackNumber == number + 1
            assert "RouteID" not in host.PropertiesList
            assert "RouteName" not in host.PropertiesList
        assert _identities(fixture.doc.analysis) == original_ids
        assert fixture.doc.config["integration_active"] is True


def validate_optional_host_metadata():
    """Preserve optional property absence and values as distinct identities."""
    fixture = _Fixture(integrated=True, route_metadata=True)
    _install_adapter(fixture)
    for radius in (900.0, 600.0):
        _run(fixture, radius)
        for number in range(2):
            host = fixture.doc.getObject("RailwayTrackCentreline_0" + str(number))
            assert host.RouteID == "route-" + str(number)
            assert host.RouteName == "Route " + str(number)
    for field in ("RouteID", "RouteName"):
        changes = (
            (False, lambda host, field=field: setattr(host, field, "")),
            (False, lambda host, field=field: setattr(host, field, "invented")),
            (True, lambda host, field=field: delattr(host, field)),
            (True, lambda host, field=field: setattr(host, field, "changed")),
        )
        for present, change in changes:
            fixture = _Fixture(integrated=True, route_metadata=present)
            _install_adapter(fixture)
            before = fixture.doc.state()
            fixture.host_change = change
            _expect_rejection(lambda: _run(fixture, 900.0))
            assert fixture.doc.state() == before, (field, present)
            assert fixture.doc.UndoCount == 0 and fixture.doc.pending is None


def validate_generate_report_history():
    """Postcommit report callbacks must not split one accepted Generate."""
    fixture = _Fixture(integrated=True, route_metadata=True)
    _install_adapter(fixture)
    _run(fixture, 900.0)
    assert not fixture.module.report_errors, fixture.module.report_errors
    assert fixture.doc.UndoCount == 1, (
        "One Generate created " + str(fixture.doc.UndoCount) + " Undo entries"
    )


def validate_generate_report_index():
    """Both reports consume the final persisted index after integration."""
    fixture = _Fixture(integrated=True, route_metadata=True)
    _install_adapter(fixture)
    _run(fixture, 900.0)
    assert not fixture.module.report_errors, fixture.module.report_errors
    for name in ("ProductionSchedule", "MaterialReport"):
        sheet = fixture.doc.getObject(name)
        assert sheet is not None
        assert sheet.Rows == fixture.doc.records, (
            name + " used the pre-dependency local index"
        )


def validate_generate_report_lifecycle():
    """Reports are current, written once, and included in atomic recovery."""
    fixture = _Fixture(integrated=True)
    _install_adapter(fixture)
    before = fixture.doc.state()
    for index, radius in enumerate((900.0, 600.0), 1):
        fixture.calls.clear()
        fixture.report_inputs.clear()
        fixture.module.report_returns.clear()
        _run(fixture, radius)
        assert not fixture.module.report_errors, fixture.module.report_errors
        assert fixture.doc.UndoCount == index
        assert len(fixture.report_inputs) == 2
        for kind, rows, in_transaction in fixture.report_inputs:
            assert in_transaction, kind + " built after Generate committed"
            assert rows == fixture.doc.records
            assert fixture.calls.count(kind + " rows built") == 1
            assert fixture.calls.count(kind + " written") == 1
        assert fixture.calls.index("analysis written") < fixture.calls.index(
            "schedule rows built") < fixture.calls.index("schedule written") < (
                fixture.calls.index("material rows built")
            ) < fixture.calls.index("material written")
        expected_names = {"schedule": "ProductionSchedule", "material": "MaterialReport"}
        assert len(fixture.module.report_returns) == 2
        for kind, sheet in fixture.module.report_returns:
            assert sheet is fixture.doc.getObject(expected_names[kind])
            assert sheet.Rows == fixture.doc.records
        after = fixture.doc.state()
        fixture.doc.undo()
        assert fixture.doc.state() == before
        fixture.doc.redo()
        assert fixture.doc.state() == after
        before = after
    for stage in ("schedule rows built", "schedule written",
                  "material rows built", "material written"):
        fixture = _Fixture(integrated=True)
        _install_adapter(fixture)
        _run(fixture, 900.0)
        before = fixture.doc.state()
        history = (fixture.doc.UndoCount, fixture.doc.RedoCount)
        fixture.fault = stage
        _expect_rejection(lambda: _run(fixture, 600.0), "Injected " + stage)
        assert fixture.doc.state() == before, stage
        assert (fixture.doc.UndoCount, fixture.doc.RedoCount) == history
        assert fixture.doc.pending is None and not fixture.module.report_errors


def validate_report_passthrough_and_binding():
    """Unrelated routes keep inherited reports; drift cannot bypass admission."""
    for mode in ("no crossover", "Create New"):
        fixture = _Fixture()
        if mode == "no crossover":
            fixture.doc.removeObject("CrossoverSettings")
        else:
            fixture.module.request["output_mode"] = fixture.module.OUTPUT_CREATE_NEW
        _install_adapter(fixture)
        _run(fixture, 900.0)
        assert fixture.doc.UndoCount == 3, mode
        assert not fixture.module.report_errors
        assert len(fixture.report_inputs) == 2
        assert all(not in_transaction for _, _, in_transaction in fixture.report_inputs)
        assert "crossover build" not in fixture.calls
    for name in _HOOKS[5:]:
        fixture = _Fixture(integrated=True)
        _install_adapter(fixture)
        setattr(fixture.module, name, lambda *_args, **_kwargs: None)
        before = fixture.doc.state()
        _expect_rejection(lambda: _run(fixture, 900.0))
        assert fixture.doc.state() == before, name
        assert fixture.doc.UndoCount == 0 and not fixture.calls
    fixture = _Fixture(integrated=True)
    _install_adapter(fixture)
    _run(fixture, 900.0)
    module = fixture.module
    rows = module.build_production_schedule_rows(
        module.read_production_record_index(fixture.doc.getObject("Settings")),
        {"enabled": False}, "SET-001",
    )
    module.create_or_replace_production_schedule(fixture.doc, "SET-001", rows)
    assert fixture.doc.UndoCount == 2, "A detached report request was suppressed"


def validate_spacing_derived_lengths():
    """Spacing-match output lengths are evaluated results, not frozen intent."""
    fixture = _Fixture(integrated=True, route_metadata=True)
    _install_adapter(fixture)
    original = _copy(fixture.module.request["track_configs"])
    for radius, length in ((900.0, 516.3161267502378),
                           (600.0, 559.4102547270278)):
        evaluated = _copy(original)
        evaluated[0].update(entry_transition_length=length,
                            exit_transition_length=length)
        fixture.evaluated_tracks = evaluated
        _run(fixture, radius)
        stored = fixture.doc.getObject("Settings").inputs["track_configs"]
        assert stored == fixture.evaluated_store_inputs[-1] == evaluated
        assert fixture.module.request["track_configs"] == original


def validate_track_intent_and_evaluated_store_guards():
    """Derived-field treatment cannot hide intent or persisted-output drift."""
    for key, value in (
        ("start_spacing", 51.0), ("curve_spacing", 56.0),
        ("finish_spacing", 51.0), ("width", 33.0),
        ("side", "Inside"), ("alignment_mode", "Euler - use lengths"),
        ("create_template", False), ("show_centreline", False),
    ):
        fixture = _Fixture(integrated=True)
        fixture.module.request["track_configs"][0][key] = value
        _install_adapter(fixture)
        before = fixture.doc.state()
        _expect_rejection(lambda: _run(fixture, 900.0))
        assert fixture.doc.state() == before, key
        assert "host replacement" not in fixture.calls, key
    for key in ("entry_transition_length", "exit_transition_length"):
        fixture = _Fixture(integrated=True)
        for tracks in (fixture.module.request["track_configs"],
                       fixture.doc.getObject("Settings").inputs["track_configs"]):
            tracks[0]["alignment_mode"] = fixture.module.MODE_USE_LENGTHS
        fixture.module.request["track_configs"][0][key] += 1.0
        _install_adapter(fixture)
        before = fixture.doc.state()
        _expect_rejection(lambda: _run(fixture, 900.0))
        assert fixture.doc.state() == before, key
        assert "host replacement" not in fixture.calls, key
    for mode in ("Euler - match spacings", "Euler - use lengths"):
        fixture = _Fixture(integrated=True)
        for tracks in (fixture.module.request["track_configs"],
                       fixture.doc.getObject("Settings").inputs["track_configs"]):
            tracks[0]["alignment_mode"] = mode
        _install_adapter(fixture)
        _run(fixture, 900.0)
        assert fixture.doc.getObject("Settings").inputs["track_configs"] == (
            fixture.evaluated_store_inputs[-1]
        )
    for drift in ("stored derived value", "evaluated intent", "explicit output"):
        fixture = _Fixture(integrated=True)
        if drift == "stored derived value":
            fixture.stored_track_change = lambda tracks: tracks[0].update(
                entry_transition_length=999.0)
        elif drift == "evaluated intent":
            fixture.evaluated_tracks = _copy(fixture.module.request["track_configs"])
            fixture.evaluated_tracks[0]["start_spacing"] += 1.0
        else:
            for tracks in (fixture.module.request["track_configs"],
                           fixture.doc.getObject("Settings").inputs["track_configs"]):
                tracks[0]["alignment_mode"] = fixture.module.MODE_USE_LENGTHS
            fixture.evaluated_tracks = _copy(fixture.module.request["track_configs"])
            fixture.evaluated_tracks[0]["exit_transition_length"] += 1.0
        _install_adapter(fixture)
        before = fixture.doc.state()
        _expect_rejection(lambda: _run(fixture, 900.0))
        assert fixture.doc.state() == before, drift
        assert fixture.doc.UndoCount == 0 and fixture.doc.pending is None


def validate_canonical_sequence():
    """Identity, current data and history survive without manual repair."""
    fixture = _Fixture()
    _install_adapter(fixture)
    initial = fixture.doc.state()
    before = initial
    ids = _identities(fixture.doc.analysis)
    preserved = (
        "crossover_id", "turnout_a_id", "turnout_b_id", "template_set_id",
        "host_a_object", "host_b_object", "reference_chainage",
        "toe_chainage_a", "arrangement", "handing", "track_gauge",
        "flangeway", "minimum_requested_radius", "timber_analysis_settings",
        "shared_timber_settings", "b3_settings", "b4_settings",
        "chair_analysis_settings",
    )
    for index, radius in enumerate((900.0, 600.0, 600.0), 1):
        _run(fixture, radius)
        doc = fixture.doc
        assert doc.radius == radius and doc.pending is None
        assert all(doc.config[key] == initial["config"][key]
                   for key in preserved)
        assert _identities(doc.analysis) == ids
        assert all(item["centre_point"][0] == radius
                   for item in doc.analysis["positions"])
        assert doc.analysis["geometry_signature"] == "radius:" + str(radius)
        assert doc.config["b4_result"]["resolved_timbers"] == [
            {"source_radius": radius},
        ]
        assert doc.UndoCount == index and doc.RedoCount == 0
        after = doc.state()
        doc.undo()
        assert doc.state() == before
        doc.redo()
        assert doc.state() == after
        before = after
    assert fixture.calls.count("crossover build") == 3
    assert fixture.calls.count("b4 written") == 3
    assert fixture.calls.count("analysis written") == 3


def validate_failures():
    """Late failures cannot commit hosts without coherent dependencies."""
    for stage in (
        "host replacement", "settings stored", "crossover build",
        "crossover committed", "catalogue written", "b4 written",
        "analysis written",
    ):
        fixture = _Fixture()
        _install_adapter(fixture)
        before = fixture.doc.state()
        fixture.fault = stage
        _expect_rejection(lambda: _run(fixture, 900.0), "Injected " + stage)
        assert fixture.doc.state() == before, stage
        assert fixture.doc.UndoCount == fixture.doc.RedoCount == 0, stage
        assert fixture.doc.pending is None, stage
    for bad_state in ("wrong host identity", "stale rebuilt analysis",
                      "changed P identity", "nested Generate"):
        fixture = _Fixture()
        _install_adapter(fixture)
        before = fixture.doc.state()
        if bad_state == "wrong host identity":
            fixture.wrong_host = True
        elif bad_state == "stale rebuilt analysis":
            fixture.stale_analysis = True
        elif bad_state == "changed P identity":
            fixture.wrong_rebuilt_ids = True
        else:
            fixture.reenter = True
        _expect_rejection(lambda: _run(fixture, 900.0))
        assert fixture.doc.state() == before, bad_state
        assert fixture.doc.UndoCount == 0 and fixture.doc.pending is None


def validate_admission():
    """Unsupported canonical intent is refused before generated deletion."""
    def config_change(key, value):
        return lambda f: f.doc.config.__setitem__(key, value)

    changes = (
        ("active without record", config_change("integration_active", True)),
        ("unknown schema", config_change("schema_version", 999)),
        ("malformed source", config_change("turnout_a_config", None)),
        ("wrong set", config_change("template_set_id", "SET-002")),
        ("unsupported gauge", config_change("track_gauge", 18.83)),
        ("missing B4", config_change("b4_result", {})),
        ("missing host", lambda f: f.doc.removeObject(
            "RailwayTrackCentreline_01")),
        ("stale source", lambda f: f.doc.analysis.__setitem__(
            "geometry_signature", "previous-host-state")),
        ("incomplete P set", lambda f: f.doc.analysis["positions"].pop()),
        ("duplicate P ID", lambda f: f.doc.analysis["positions"][0].update(
            f.doc.analysis["positions"][1])),
        ("extra XO", lambda f: f.extra_crossovers.append({
            **_copy(f.doc.config), "crossover_id": "XO-002"})),
        ("extra turnout", lambda f: f.extra_turnouts.append({
            "turnout_id": "TO-999", "template_set_id": "SET-001"})),
        ("changed angle", lambda f: f.module.request.__setitem__(
            "angle", 91.0)),
        ("export enabled", lambda f: f.module.request.__setitem__(
            "production_export_config", {"enabled": True})),
        ("Undo disabled", lambda f: setattr(f.doc, "UndoMode", 0)),
    )
    for label, change in changes:
        fixture = _Fixture()
        change(fixture)
        _install_adapter(fixture)
        before = fixture.doc.state()
        _expect_rejection(lambda: _run(fixture, 900.0))
        assert fixture.doc.state() == before, label
        assert "host replacement" not in fixture.calls, label
        assert fixture.doc.pending is None and fixture.doc.UndoCount == 0
    for radius in (math.nan, math.inf, -math.inf, 0.0, -1.0):
        fixture = _Fixture()
        _install_adapter(fixture)
        before = fixture.doc.state()
        _expect_rejection(lambda: _run(fixture, radius))
        assert fixture.doc.state() == before
        assert "host replacement" not in fixture.calls
    for malformed in ("crossover", "extra turnout", "extra set"):
        fixture = _Fixture()
        if malformed == "crossover":
            fixture.doc.config = None
            obj = fixture.doc.getObject("CrossoverSettings")
            del obj.CrossoverID
            obj.CrossoverConfigJSON = "{ invalid JSON"
        elif malformed == "extra turnout":
            obj = _Object("UnparsedTurnout", "TurnoutSettings")
            obj.TurnoutConfigJSON = "{ invalid JSON"
            fixture.doc.Objects.append(obj)
        else:
            obj = _Object("OtherSetSettings", "Settings")
            obj.TemplateSetID = "SET-002"
            fixture.doc.Objects.append(obj)
        _install_adapter(fixture)
        before = fixture.doc.state()
        _expect_rejection(lambda: _run(fixture, 900.0))
        assert fixture.doc.state() == before, malformed
        assert "host replacement" not in fixture.calls, malformed


def validate_integration_sequence():
    """Preserve existing integration intent, regenerating its derived records."""
    fixture = _Fixture(integrated=True)
    _install_adapter(fixture)
    before = fixture.doc.state()
    original_ids = _identities(fixture.doc.analysis)
    for index, radius in enumerate((900.0, 600.0), 1):
        fixture.calls.clear()
        _run(fixture, radius)
        doc = fixture.doc
        record = fixture._integration_by_id(doc, "XO-001")
        assert doc.config["integration_active"] is True
        assert doc.config["production_ready"] is False
        assert record == doc.config["integration_result"]
        assert record["signature"] == "integration:" + str(radius)
        assert record["b4_signature"] == "b4:" + str(radius)
        assert set(record["source_record_ids"]) == {
            "host/current", "XO-001/current",
        }
        metadata = (record["original_host_record_metadata"]
                    + record["original_crossover_record_metadata"])
        assert all(item["source_radius"] == radius for item in metadata)
        roles = {obj.GeneratedRole for obj in
                 fixture._integration_objects(doc, "XO-001")}
        assert roles == set(INTEGRATION_ROLES.values())
        assert len(record["integration_object_names"]) == 6
        assert len(doc.records) == 3
        assert {doc.getObject(item["source_name"]).GeneratedRole
                for item in doc.records} == {
            "CrossoverIntegratedHostTemplate", "CrossoverIntegratedHostOutline",
            "CrossoverIntegratedResolvedTimberGeometry",
        }
        for item in doc.records:
            assert item["source_radius"] == radius
            assert item["record_id"] in json.loads(
                doc.getObject(item["source_name"]).ProductionRecordIDsJSON,
            )
        assert doc.getObject("HostTemplate").Visibility is False
        assert doc.getObject("CrossoverTemplate").Visibility is False
        assert doc.getObject("ForeignWitness").Visibility is True
        assert fixture.calls.index("b4 written") < fixture.calls.index(
            "integration records written") < fixture.calls.index(
                "integration visibility written") < fixture.calls.index(
                    "analysis written")
        assert fixture.calls.count("integration records written") == 1
        assert fixture.calls.count("analysis written") == 1
        assert _identities(doc.analysis) == original_ids
        assert all(item["centre_point"][0] == radius
                   for item in doc.analysis["positions"])
        assert doc.UndoCount == index and doc.RedoCount == 0
        after = doc.state()
        doc.undo()
        assert doc.state() == before
        doc.redo()
        assert doc.state() == after
        before = after


def _rewrite_integration_record(fixture, change):
    """Alter a declared record consistently, without bypassing admission."""
    record = fixture._integration_by_id(fixture.doc, "XO-001")
    change(record)
    fixture.doc.config["integration_result"] = _copy(record)
    for obj in fixture._integration_objects(fixture.doc, "XO-001"):
        obj.CrossoverHostIntegrationJSON = json.dumps(record, sort_keys=True)


def validate_integration_admission_and_rollback():
    """Malformed reversible state cannot be deleted or silently discarded."""
    def record_change(change):
        return lambda fixture: _rewrite_integration_record(fixture, change)

    changes = (
        ("missing settings", lambda f: f.doc.removeObject("Integration1")),
        ("conflicting record", lambda f: f.doc.config[
            "integration_result"].update(signature="conflicting")),
        ("stale record", record_change(lambda r: r.update(signature="stale"))),
        ("record schema", record_change(lambda r: r.update(schema_version=9))),
        ("record identity", record_change(lambda r: r.update(crossover_id="XO-002"))),
        ("record B4", record_change(lambda r: r.update(b4_signature="old-B4"))),
        ("duplicate source ID", record_change(lambda r: r[
            "source_record_ids"].append(r["source_record_ids"][0]))),
        ("missing original metadata", record_change(lambda r: r.update(
            original_host_record_metadata=[]))),
        ("unknown original source", record_change(lambda r: r[
            "original_host_record_metadata"][0].update(source_name="Missing"))),
        ("unrestorable shape", lambda f: setattr(f, "broken_hydration", True)),
        ("orphan role", lambda f: delattr(f.doc.getObject("Integration1"),
                                        "CrossoverID")),
        ("role substitution", lambda f: setattr(f.doc.getObject("Integration3"),
                                               "GeneratedRole", "Unrelated")),
        ("missing integrated catalogue", lambda f: f.doc.records.clear()),
        ("wrong integrated binding", lambda f: f.doc.records[0].update(
            source_name="Integration2")),
        ("retained replaced record", lambda f: f.doc.records.append({
            "record_id": "host/current", "source_name": "HostTemplate",
            "template_set_id": "SET-001"})),
        ("non-boolean active", lambda f: f.doc.config.update(integration_active=1)),
        ("production ready", lambda f: f.doc.config.update(production_ready=True)),
        ("inactive with records", lambda f: f.doc.config.update(integration_active=False)),
    )
    for label, change in changes:
        fixture = _Fixture(integrated=True)
        change(fixture)
        _install_adapter(fixture)
        before = fixture.doc.state()
        _expect_rejection(lambda: _run(fixture, 900.0))
        assert fixture.doc.state() == before, label
        assert fixture.doc.UndoCount == 0 and fixture.doc.pending is None
        assert "host replacement" not in fixture.calls, label
    fixture = _Fixture()
    fixture.doc.removeObject("CrossoverSettings")
    fixture.doc.Objects.append(_Object("OrphanIntegration", "CrossoverHostIntegrationSettings"))
    _install_adapter(fixture)
    before = fixture.doc.state()
    _expect_rejection(lambda: _run(fixture, 900.0))
    assert fixture.doc.state() == before
    assert "host replacement" not in fixture.calls
    for stage in ("integration records written", "integration visibility written",
                  "analysis written"):
        fixture = _Fixture(integrated=True)
        _install_adapter(fixture)
        before = fixture.doc.state()
        fixture.fault = stage
        _expect_rejection(lambda: _run(fixture, 900.0), "Injected " + stage)
        assert fixture.doc.state() == before, stage
        assert fixture.doc.UndoCount == 0 and fixture.doc.pending is None
    fixture = _Fixture(integrated=True)
    _install_adapter(fixture)
    before = fixture.doc.state()
    fixture.stale_rebuilt_integration = True
    _expect_rejection(lambda: _run(fixture, 900.0))
    assert fixture.doc.state() == before
    assert fixture.doc.UndoCount == 0 and fixture.doc.pending is None


def validate_metadata_preservation():
    """Host regeneration must not erase existing crossover edit history."""
    for integrated in (False, True):
        for side in ("A", "B"):
            fixture = _Fixture(integrated=integrated)
            expected = {
                "edit_revision": 4,
                "edited_from_macro_version": "10.2A8A7B15",
                "preferred_reversion_side": side,
            }
            fixture.doc.config.update(expected)
            _install_adapter(fixture)
            for radius in (900.0, 600.0):
                _run(fixture, radius)
                assert {key: fixture.doc.config.get(key) for key in expected} == (
                    expected
                ), "Canonical edit/reversion metadata was discarded"


def validate_metadata_admission():
    """Unknown extension semantics must fail before canonical replacement."""
    changes = [
        ("edit_revision", value) for value in (-1, True, 1.5, "4", None)
    ] + [
        ("edited_from_macro_version", 15),
        ("preferred_reversion_side", "C"),
        ("preferred_reversion_side", None),
    ] + [(key, value) for key in EXTENSION_METADATA for value in ("", None)]
    for key, value in changes:
        fixture = _Fixture()
        fixture.doc.config[key] = value
        _install_adapter(fixture)
        before = fixture.doc.state()
        _expect_rejection(lambda: _run(fixture, 900.0))
        assert fixture.doc.state() == before, (key, value)
        assert "host replacement" not in fixture.calls, (key, value)
        assert fixture.doc.UndoCount == 0 and fixture.doc.pending is None


def validate_unaffected_routes():
    """Cancellation, Create New and a source without XO keep their routes."""
    for cancellation in ("cancelled", "replace_cancelled"):
        fixture = _Fixture()
        _install_adapter(fixture)
        setattr(fixture.module, cancellation, True)
        before = fixture.doc.state()
        _run(fixture, 900.0)
        assert fixture.doc.state() == before
        assert fixture.doc.UndoCount == 0 and not fixture.calls
    fixture = _Fixture()
    _install_adapter(fixture)
    fixture.module.request["output_mode"] = fixture.module.OUTPUT_CREATE_NEW
    config = _copy(fixture.doc.config)
    _run(fixture, 900.0)
    assert fixture.doc.config == config
    assert "crossover build" not in fixture.calls
    fixture = _Fixture()
    fixture.doc.removeObject("CrossoverSettings")
    _install_adapter(fixture)
    fixture.module.request["angle"] = 91.0
    _run(fixture, 900.0)
    assert fixture.doc.radius == 900.0 and fixture.doc.config is None
    assert "crossover build" not in fixture.calls


def validate_binding():
    """A drifted host callback must not silently bypass admission."""
    from tracktemplate.compatibility.crossover_dependent_recalculation import (
        CrossoverDependentRecalculationAdapter,
    )

    fixture = _Fixture()
    _expect_rejection(lambda: CrossoverDependentRecalculationAdapter(
        fixture.module, lambda: None,
    ))
    _install_adapter(fixture)
    original = fixture.module.remove_all_generated_outputs
    fixture.module.remove_all_generated_outputs = lambda _doc: []
    before = fixture.doc.state()
    _expect_rejection(lambda: _run(fixture, 900.0))
    assert fixture.doc.state() == before
    assert fixture.module.remove_all_generated_outputs is not original


def validate_invocation_isolation():
    """Cancelled or failed accepted inputs cannot contaminate a later run."""
    for previous in ("cancelled replacement", "rejected export", "late failure"):
        fixture = _Fixture()
        _install_adapter(fixture)
        before = fixture.doc.state()
        if previous == "cancelled replacement":
            fixture.module.replace_cancelled = True
            _run(fixture, 900.0)
            fixture.module.replace_cancelled = False
        elif previous == "rejected export":
            fixture.module.request["production_export_config"] = {
                "enabled": True,
            }
            _expect_rejection(lambda: _run(fixture, 900.0))
            fixture.module.request["production_export_config"] = {
                "enabled": False,
            }
        else:
            fixture.fault = "b4 written"
            _expect_rejection(lambda: _run(fixture, 900.0), "Injected b4")
            fixture.fault = None
        assert fixture.doc.state() == before
        calls = list(fixture.calls)
        fixture.module._document_recompute(fixture.doc)
        assert fixture.doc.state() == before
        assert fixture.calls == calls, "Detached recompute consumed old intent"
        fixture.calls.clear()
        _run(fixture, 900.0)
        assert fixture.doc.radius == 900.0
        assert fixture.doc.UndoCount == 1
        assert fixture.calls.count("crossover build") == 1
        assert fixture.calls.count("b4 written") == 1
        assert fixture.calls.count("analysis written") == 1
    fixture = _Fixture()
    _install_adapter(fixture)
    fixture.module.replace_cancelled = True
    _run(fixture, 900.0)
    first = fixture.doc.state()
    second = _FixtureDocument()
    second.Name = "OtherSource"
    second.removeObject("CrossoverSettings")
    fixture.module.App.ActiveDocument = second
    fixture.module.replace_cancelled = False
    _run(fixture, 900.0)
    assert second.radius == 900.0 and second.config is None
    assert fixture.doc.state() == first, "A different document was mutated"
    assert "crossover build" not in fixture.calls


def validate():
    """Run focused orchestration contracts, without geometry acceptance."""
    validate_binding()
    validate_curved_host_without_route()
    validate_optional_host_metadata()
    validate_generate_report_history()
    validate_generate_report_index()
    validate_generate_report_lifecycle()
    validate_report_passthrough_and_binding()
    validate_spacing_derived_lengths()
    validate_track_intent_and_evaluated_store_guards()
    validate_canonical_sequence()
    validate_failures()
    validate_admission()
    validate_integration_sequence()
    validate_integration_admission_and_rollback()
    validate_metadata_preservation()
    validate_metadata_admission()
    validate_unaffected_routes()
    validate_invocation_isolation()
    print(SENTINEL)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-witness", action="store_true")
    arguments = parser.parse_args()
    if arguments.legacy_witness:
        legacy_deletion_witness()
        raise AssertionError("Legacy deletion witness unexpectedly passed")
    validate()


if __name__ == "__main__":
    main()
