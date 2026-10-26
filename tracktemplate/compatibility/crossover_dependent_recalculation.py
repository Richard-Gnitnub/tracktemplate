"""Preserve one qualified crossover through explicit host regeneration.

Generate remains the inherited explicit template-materialisation command.
Its dependent B4 and chair analysis run inside the same transaction. Private
catalogue chair geometry still requires a separate preview request.
"""

import copy
import inspect
import json
import math
import sys

from tracktemplate.compatibility.chair_catalogue_placement import (
    _require_p_crossover_context,
    _select_p_positions,
)
from tracktemplate.compatibility.chair_reference_preview import (
    _source_context,
)
from tracktemplate.compatibility.crossover_host_integration_recovery import (
    CrossoverHostIntegrationRecoveryAdapter,
)


HOOK_NAMES = (
    "remember_last_dialog_inputs", "validate_production_export_request",
    "remove_all_generated_outputs", "store_parameters",
    "_document_recompute",
    "build_production_schedule_rows", "create_or_replace_production_schedule",
    "build_material_report_rows", "create_or_replace_material_report",
)
_OPTION_READERS = (
    ("straight_configs", "read_straight_configs"),
    ("platform_configs", "read_platform_configs"),
    ("formation_config", "read_formation_config"),
    ("section_config", "read_section_config"),
    ("registration_config", "read_registration_config"),
    ("template_assembly_config", "read_template_assembly_config"),
    ("production_export_config", "read_production_export_config"),
)
_DEPENDENT_SETTINGS = (
    "timber_analysis_settings", "shared_timber_settings", "b3_settings",
    "b4_settings", "chair_analysis_settings",
)
_HOST_PROPERTIES = (
    "GeneratedBy", "GeneratedRole", "TemplateSetID", "RouteID", "RouteName",
    "TrackName", "ExportSubtype",
)
_PRESERVED_METADATA = (
    "edit_revision", "edited_from_macro_version", "preferred_reversion_side",
)
_UNSUPPORTED_EXTENSION_METADATA = (
    "extended_from_turnout_id", "extension_preserved_toe_chainage",
    "extension_preserved_handing", "extension_preserved_orientation",
    "extension_mode", "conversion_source_turnout_config",
)
_INTEGRATION_ROLE_NAMES = (
    "CROSSOVER_INTEGRATION_GROUP_ROLE",
    "CROSSOVER_INTEGRATION_SETTINGS_ROLE",
    "CROSSOVER_INTEGRATED_DISPLAY_ROLE",
    "CROSSOVER_INTEGRATED_TEMPLATE_ROLE",
    "CROSSOVER_INTEGRATED_OUTLINE_ROLE",
    "CROSSOVER_INTEGRATED_TIMBER_ROLE",
)


class CrossoverDependentRecalculationError(ValueError):
    """Generate cannot preserve the existing canonical dependency safely."""


def _require(condition, message):
    if not condition:
        raise CrossoverDependentRecalculationError(
            "Crossover dependent recalculation: " + message
        )


class _ChildTransactionDocument:
    """Keep one inherited child operation inside Generate's transaction."""

    def __init__(self, document, expected_label):
        self._document = document
        self._expected_label = expected_label
        self.opened = False
        self.committed = False
        self.aborted = False

    def __getattr__(self, name):
        return getattr(self._document, name)

    def openTransaction(self, label):
        _require(not self.opened and label == self._expected_label,
                 "a dependent transaction boundary changed")
        self.opened = True

    def commitTransaction(self):
        _require(self.opened and not self.committed and not self.aborted,
                 "a dependent transaction commit changed")
        self.committed = True

    def abortTransaction(self):
        _require(self.opened and not self.committed and not self.aborted,
                 "a dependent transaction abort changed")
        self.aborted = True

    def require_committed(self):
        _require(self.opened and self.committed and not self.aborted,
                 "a dependent operation did not commit exactly once")


class CrossoverDependentRecalculationAdapter:
    """Bind the original Generate caller without replacing its function.

    Hooks recognise the original caller and one accepted request's integer
    frame token. No frame or document reference is retained. Failed request
    data cannot be consumed by another invocation; its next accepted request
    replaces it. Cancellation never reaches the deletion boundary.
    """

    def __init__(self, module, original_generate):
        self.module = module
        self.original_generate = original_generate
        self.originals = {
            name: getattr(module, name) for name in HOOK_NAMES
        }
        self.bindings = dict(zip(HOOK_NAMES, (
            self._remember, self._validate_export, self._remove,
            self._store, self._recompute,
            self._schedule_rows, self._schedule,
            self._material_rows, self._material,
        )))
        self._pending = None
        self.validate_originals()

    def validate_originals(self):
        namespace = self.module.__dict__
        caller = self.original_generate
        code = getattr(caller, "__code__", None)
        _require(callable(caller) and code is not None
                 and getattr(caller, "__globals__", None) is namespace
                 and set(HOOK_NAMES) <= set(code.co_names),
                 "the inherited Generate caller changed")
        for name, function in self.originals.items():
            _require(callable(function)
                     and getattr(function, "__globals__", None) is namespace,
                     "the inherited {} hook changed".format(name))

    def validate_binding(self):
        self.validate_originals()
        namespace = self.module.__dict__
        _require(namespace.get("run_macro") is self.original_generate,
                 "the inherited Generate function was replaced")
        for name, function in self.bindings.items():
            _require(namespace.get(name) is function,
                     "the {} binding changed".format(name))

    def _invocation(self):
        frame = sys._getframe(2)
        try:
            if (frame.f_code is self.original_generate.__code__
                    and frame.f_globals is self.module.__dict__):
                return id(frame)
            return None
        finally:
            del frame

    def _require_not_reentrant(self, token):
        pending = self._pending
        if pending is None or pending["token"] == token:
            return
        frame = sys._getframe(1)
        try:
            while frame is not None:
                if (frame.f_code is self.original_generate.__code__
                        and frame.f_globals is self.module.__dict__):
                    _require(id(frame) != pending["token"],
                             "nested Generate requests are unsupported")
                frame = frame.f_back
        finally:
            del frame

    def _request(self, token):
        pending = self._pending
        if (token is not None and pending is not None
                and pending["token"] == token):
            return pending
        return None

    def _caller_request(self, token, *, validated=True):
        if token is None:
            return None
        self.validate_binding()
        pending = self._request(token)
        _require(pending is not None,
                 "the accepted Generate request was not captured")
        if validated:
            _require(pending["validated"],
                     "the Generate request was not validated")
        return pending

    def _remember(self, *args, **kwargs):
        token = self._invocation()
        if token is not None:
            self.validate_binding()
            self._require_not_reentrant(token)
            bound = inspect.signature(self.originals[HOOK_NAMES[0]]).bind(
                *args, **kwargs,
            )
            bound.apply_defaults()
            request = dict(bound.arguments)
            document = request.pop("doc")
            self._pending = {
                "token": token, "document_id": id(document),
                "document_name": str(document.Name),
                "request": copy.deepcopy(request), "source": None,
                "validated": False,
                "removed": False, "stored": False,
                "finalising": False, "finalised": False,
                "evaluated_track_configs": None, "reports": None,
            }
        return self.originals[HOOK_NAMES[0]](*args, **kwargs)

    def _host_options(self, document):
        module = self.module
        settings = module.latest_generated_settings(document)
        _require(settings is not None, "canonical host settings are missing")
        values = {}
        for name, property_name in (
            ("transition", "TransitionLength"),
            ("radius", "CurveRadius"), ("angle", "TotalTurnAngle"),
            ("main_width", "MainTemplateWidth"),
        ):
            value = module.quantity_value(settings, property_name, math.nan)
            _require(isinstance(value, (int, float))
                     and not isinstance(value, bool) and math.isfinite(value),
                     "canonical {} is invalid".format(property_name))
            values[name] = value
        values["track_configs"] = module.read_track_configs(
            settings, values["transition"],
        )
        for name, reader in _OPTION_READERS:
            values[name] = getattr(module, reader)(settings)
        return copy.deepcopy(values)

    def _active_track_intent(self, configs):
        """Separate matching-mode calculated lengths from its input intent."""
        intent = copy.deepcopy(configs)
        for config in intent:
            if config.get("alignment_mode") == self.module.MODE_MATCH_SPACINGS:
                config.pop("entry_transition_length", None)
                config.pop("exit_transition_length", None)
        return intent

    def _options_match_intent(self, options, request, *, ignore_radius=False):
        for name, value in options.items():
            if ignore_radius and name == "radius":
                continue
            if name == "track_configs":
                if (self._active_track_intent(value)
                        != self._active_track_intent(request[name])):
                    return False
            elif value != request[name]:
                return False
        return True

    def _host_identity(self, document, name):
        module = self.module
        host = document.getObject(name)
        _require(host is not None and module.is_turnout_host_centreline(host),
                 "a canonical crossover host is missing or unsupported")
        identity = {field: module.object_string_property(host, field, "")
                    for field in _HOST_PROPERTIES}
        identity["name"] = str(host.Name)
        identity["track_number"] = module._integer_object_property(
            host, "TrackNumber", 0,
        )
        identity["route_properties_present"] = tuple(
            name for name in ("RouteID", "RouteName") if hasattr(host, name)
        )
        _require(identity["GeneratedBy"] == module.GENERATOR_ID
                 and identity["TemplateSetID"] == "SET-001"
                 and identity["GeneratedRole"],
                 "the canonical host identity is incomplete")
        return identity

    def _source(self, document):
        module = self.module
        signature, analysis, settings, plan, rails, timbers = _source_context(
            module, document, "XO-001", "P", entity_kind="crossover",
        )
        context = json.loads(signature)
        owners = _require_p_crossover_context(
            module, context, "XO-001", settings, plan,
        )
        placements, _selected, _excluded, _base_z = _select_p_positions(
            module, analysis, plan, rails, timbers, "XO-001",
            crossover_owners=owners,
        )
        identities = sorted(item.position_id for item in placements)
        _require(len(identities) == len(set(identities)) == 28,
                 "the qualified 28 P positions are incomplete")
        return {
            "signature": signature, "config": context["configuration"],
            "p_identities": identities,
        }

    def _canonical_metadata(self, config):
        _require(not any(key in config
                         for key in _UNSUPPORTED_EXTENSION_METADATA),
                 "extension or conversion provenance is unsupported")
        if "edit_revision" in config:
            revision = config["edit_revision"]
            _require(type(revision) is int and revision >= 0,
                     "the crossover edit revision is invalid")
        if "edited_from_macro_version" in config:
            _require(isinstance(config["edited_from_macro_version"], str),
                     "the crossover edit version is invalid")
        if "preferred_reversion_side" in config:
            _require(config["preferred_reversion_side"] in (
                self.module.CROSSOVER_REVERSION_SIDE_A,
                self.module.CROSSOVER_REVERSION_SIDE_B,
            ), "the preferred crossover reversion side is invalid")
        return {key: copy.deepcopy(config[key]) for key in _PRESERVED_METADATA
                if key in config}

    def _integration_objects(self, document):
        roles = {getattr(self.module, name)
                 for name in _INTEGRATION_ROLE_NAMES}
        return [obj for obj in document.Objects
                if self.module.object_string_property(
                    obj, "GeneratedRole", "",
                ) in roles]

    def _integration_state(self, document, config):
        """Validate reversible state without trusting its active flag alone."""
        module = self.module
        active = config.get("integration_active")
        _require(type(active) is bool and config.get("production_ready")
                 is False, "the crossover integration authority is invalid")
        objects = self._integration_objects(document)
        record = module.crossover_host_integration_by_id(document, "XO-001")
        if not active:
            _require(not objects and record is None
                     and not config.get("integration_result")
                     and not config.get("integration_signature"),
                     "inactive crossover integration has retained state")
            return None
        create = module.create_crossover_host_integration
        recovery = getattr(create, "__self__", None)
        _require(type(recovery) is CrossoverHostIntegrationRecoveryAdapter
                 and recovery.module is module
                 and getattr(create, "__func__", None)
                 is CrossoverHostIntegrationRecoveryAdapter.create,
                 "the recoverable integration command binding changed")
        status = module.CROSSOVER_INTEGRATION_STATUS_ACTIVE
        _require(isinstance(record, dict)
                 and type(record.get("schema_version")) is int
                 and record["schema_version"]
                 == module.CROSSOVER_INTEGRATION_SCHEMA_VERSION
                 and config.get("integration_schema_version")
                 == record["schema_version"]
                 and record.get("crossover_id") == "XO-001"
                 and record.get("template_set_id") == "SET-001"
                 and record.get("status") == status
                 and config.get("integration_status") == status
                 and config.get("integration_result") == record
                 and record.get("b4_signature")
                 == config["b4_result"].get("resolution_signature"),
                 "the reversible integration record is inconsistent")
        names = record.get("integration_object_names")
        roles = [getattr(module, name) for name in _INTEGRATION_ROLE_NAMES]
        _require(isinstance(names, list)
                 and all(isinstance(name, str) and name for name in names)
                 and len(names) == len(set(names)) == len(roles)
                 and sorted(names) == sorted(str(obj.Name) for obj in objects)
                 and sorted(roles) == sorted(module.object_string_property(
                     obj, "GeneratedRole", "",
                 ) for obj in objects)
                 and all(module.object_string_property(
                     obj, "GeneratedBy", "",
                 ) == module.GENERATOR_ID
                     and module.object_string_property(
                         obj, module.CROSSOVER_ID_PROPERTY, "",
                     ) == "XO-001"
                     and module.object_string_property(
                         obj, "TemplateSetID", "",
                     ) == "SET-001" for obj in objects),
                 "the complete integration object ownership is invalid")
        for key in ("source_visibility", "crossover_visibility"):
            visibility = record.get(key)
            _require(isinstance(visibility, dict) and visibility
                     and all(isinstance(name, str) and name
                             and document.getObject(name) is not None
                             and (value is None or type(value) is bool)
                             for name, value in visibility.items()),
                     "reversible integration visibility is incomplete")
        metadata = []
        for key in ("original_host_record_metadata",
                    "original_crossover_record_metadata"):
            items = record.get(key)
            _require(isinstance(items, list) and items
                     and all(isinstance(item, dict) for item in items),
                     "original integration record metadata is missing")
            metadata.extend(items)
        _require(all(isinstance(item.get("record_id"), str)
                     and item["record_id"]
                     and isinstance(item.get("source_name"), str)
                     and item["source_name"]
                     and document.getObject(item["source_name"]) is not None
                     and item.get("template_set_id") == "SET-001"
                     for item in metadata),
                 "an original integration source binding is invalid")
        source_ids = record.get("source_record_ids")
        metadata_ids = [item["record_id"] for item in metadata]
        _require(isinstance(source_ids, list)
                 and all(isinstance(value, str) and value
                         for value in source_ids)
                 and len(source_ids) == len(set(source_ids))
                 == len(metadata_ids) == len(set(metadata_ids))
                 and set(source_ids) == set(metadata_ids),
                 "original integration source identities are incomplete")
        settings = module.settings_for_template_set(document, "SET-001")
        _require(settings is not None,
                 "the integrated production catalogue is missing")
        index = module.read_production_record_index(settings)
        current_records = (index.get("records")
                           if isinstance(index, dict) else None)
        _require(isinstance(current_records, list)
                 and all(isinstance(item, dict) for item in current_records),
                 "the integrated production catalogue is invalid")
        integrated = [item for item in current_records
                      if item.get("source_name") in names]
        production_names = {str(obj.Name) for obj in objects
                            if module.object_string_property(
                                obj, "GeneratedRole", "",
                            ) in roles[3:]}
        _require(len(integrated) == len(production_names)
                 and {item.get("source_name") for item in integrated}
                 == production_names
                 and all(isinstance(item.get("record_id"), str)
                         and item["record_id"]
                         and item.get("template_set_id") == "SET-001"
                         for item in integrated)
                 and len({item["record_id"] for item in integrated})
                 == len(integrated)
                 and not any(item.get("record_id") in source_ids
                             for item in current_records),
                 "the integrated production record replacement is invalid")
        restored = module._crossover_integration_restored_records(
            document, record,
        )
        originals = [item for item in restored
                     if item.get("record_id") in source_ids]
        _require(len(originals) == len(metadata)
                 and all(item.get("shape") is not None for item in originals)
                 and sorted((item["record_id"], item.get("source_name"))
                            for item in originals)
                 == sorted((item["record_id"], item["source_name"])
                           for item in metadata),
                 "the original integration sources cannot be restored")
        _require(module.crossover_host_integration_effective_status(
            document, config,
        ) == status, "the crossover host integration is stale")
        return copy.deepcopy(record)

    def _validate_export(self, *args, **kwargs):
        pending = self._caller_request(self._invocation(), validated=False)
        result = self.originals[HOOK_NAMES[1]](*args, **kwargs)
        if pending is None:
            return result
        request = pending["request"]
        module = self.module
        if request["output_mode"] != module.OUTPUT_REPLACE:
            pending["validated"] = True
            return result
        document = module.App.ActiveDocument
        _require(document is not None and id(document)
                 == pending["document_id"], "the Generate document changed")
        configs = module.existing_crossover_configs(document)
        tagged = [obj for obj in document.Objects
                  if module.object_string_property(
                      obj, module.CROSSOVER_ID_PROPERTY, "",
                  )]
        crossover_settings = [obj for obj in document.Objects
                              if module.object_string_property(
                                  obj, "GeneratedRole", "",
                              ) == module.CROSSOVER_SETTINGS_ROLE]
        turnout_settings = [obj for obj in document.Objects
                            if module.object_string_property(
                                obj, "GeneratedRole", "",
                            ) == module.TURNOUT_SETTINGS_ROLE]
        if (not configs and not tagged and not crossover_settings
                and not self._integration_objects(document)):
            pending["validated"] = True
            return result
        _require(not request["production_export_config"].get("enabled"),
                 "dependent Generate does not admit production export")
        _require(int(document.UndoMode) == 1,
                 "enable document Undo before replacing crossover hosts")
        _require(len(configs) == len(crossover_settings) == 1
                 and not turnout_settings
                 and not module.existing_turnout_configs(document),
                 "the complete dependent set is not qualified")
        config = configs[0]
        _require(config.get("crossover_id") == "XO-001"
                 and config.get("template_set_id") == "SET-001"
                 and type(config.get("schema_version")) is int
                 and config["schema_version"]
                 == module.CROSSOVER_SCHEMA_VERSION,
                 "the crossover configuration is unsupported")
        metadata = self._canonical_metadata(config)
        _require(all(module.object_string_property(
            obj, module.CROSSOVER_ID_PROPERTY, "",
        ) == "XO-001" for obj in tagged),
            "another crossover dependency would be removed")
        _require(all(module.object_string_property(
            obj, "TemplateSetID", "",
        ) == "SET-001" for obj in document.Objects
            if module.object_string_property(obj, "GeneratedBy", "")
            == module.GENERATOR_ID),
            "another generated template set would be removed")
        before_options = self._host_options(document)
        _require(self._options_match_intent(
            before_options, request, ignore_radius=True,
        ),
                 "only host CurveRadius may change in this dependent route")
        radius = request["radius"]
        _require(isinstance(radius, (int, float))
                 and not isinstance(radius, bool) and math.isfinite(radius)
                 and radius > 0, "the requested radius is invalid")
        source = self._source(document)
        _require(source["config"] == config,
                 "canonical crossover configuration is inconsistent")
        source["metadata"] = metadata
        source["integration"] = self._integration_state(document, config)
        for field in _DEPENDENT_SETTINGS:
            _require(isinstance(config.get(field), dict),
                     "canonical {} is missing".format(field))
        hosts = {}
        for side in ("a", "b"):
            name = config["host_" + side + "_object"]
            _require(config["turnout_" + side + "_config"]["host_object"]
                     == name, "constituent host identities disagree")
            hosts[side] = self._host_identity(document, name)
        _require(hosts["a"]["name"] != hosts["b"]["name"],
                 "the crossover hosts are not distinct")
        source["hosts"] = hosts
        pending["source"] = source
        pending["validated"] = True
        return result

    def _remove(self, document):
        pending = self._caller_request(self._invocation())
        if pending is not None and pending["source"] is not None:
            _require(id(document) == pending["document_id"]
                     and not pending["removed"],
                     "the Generate deletion boundary changed")
            current = self._source(document)
            _require(current["signature"]
                     == pending["source"]["signature"],
                     "the crossover changed before host replacement")
            _require(self._integration_state(document, current["config"])
                     == pending["source"]["integration"],
                     "integration changed before host replacement")
            pending["removed"] = True
        return self.originals[HOOK_NAMES[2]](document)

    def _store(self, *args, **kwargs):
        pending = self._caller_request(self._invocation())
        storing_settings = False
        if pending is not None and pending["source"] is not None:
            bound = inspect.signature(self.originals[HOOK_NAMES[3]]).bind(
                *args, **kwargs,
            )
            obj = bound.arguments["obj"]
            storing_settings = self.module.object_string_property(
                obj, "GeneratedRole", "",
            ) == "Settings"
            if storing_settings:
                _require(pending["removed"] and not pending["stored"]
                         and id(obj.Document) == pending["document_id"],
                         "the replacement settings boundary changed")
                # These values already came from the accepted alignment
                # calculation. Capture before the writer can alter them.
                pending["evaluated_track_configs"] = copy.deepcopy(
                    bound.arguments["track_configs"],
                )
        result = self.originals[HOOK_NAMES[3]](*args, **kwargs)
        if pending is not None:
            self.validate_binding()
        if storing_settings:
            pending["stored"] = True
        return result

    def _rebuild(self, document, pending):
        module = self.module
        source = pending["source"]
        old = source["config"]
        options = self._host_options(document)
        _require(self._options_match_intent(options, pending["request"])
                 and options["track_configs"]
                 == pending["evaluated_track_configs"],
                 "replacement host settings disagree with the request")
        hosts = []
        for side in ("a", "b"):
            identity = source["hosts"][side]
            _require(self._host_identity(document, identity["name"])
                     == identity, "a replacement host identity changed")
            hosts.append(document.getObject(identity["name"]))
        built = module._build_rea_c10_crossover_geometry(
            document, *hosts, old["reference_chainage"],
            old["arrangement"], old["handing"], old["track_gauge"],
            old["flangeway"], old["minimum_requested_radius"],
            crossover_id=old["crossover_id"],
            turnout_a_id_override=old["turnout_a_id"],
        )
        config = built["config"]
        for field in (
            "crossover_id", "template_set_id", "host_a_object",
            "host_b_object", "turnout_a_id", "turnout_b_id",
            "reference_chainage", "toe_chainage_a", "arrangement",
            "handing", "track_gauge", "flangeway",
            "minimum_requested_radius",
        ):
            _require(config.get(field) == old.get(field),
                     "recalculation changed canonical {}".format(field))
        for field in _DEPENDENT_SETTINGS:
            config[field] = copy.deepcopy(old[field])
        for field in _PRESERVED_METADATA:
            config.pop(field, None)
        config.update(copy.deepcopy(source["metadata"]))
        committed = module._commit_rea_c10_crossover_objects(document, built)
        module._turnout_store_production_records(
            document, built["set_id"], committed["records"],
        )
        module._crossover_store_catalogue(document, built["set_id"])
        child = _ChildTransactionDocument(
            document, "Apply Version {} hybrid timbering XO-001".format(
                module.MACRO_VERSION_NUMBER,
            ),
        )
        module.apply_crossover_b4_timbering(
            child, "XO-001", old["shared_timber_settings"],
            old["b3_settings"], old["b4_settings"],
        )
        child.require_committed()
        if source["integration"] is not None:
            child = _ChildTransactionDocument(
                document,
                "Integrate Version {} crossover XO-001 with host templates"
                .format(module.MACRO_VERSION_NUMBER),
            )
            integrated = module.create_crossover_host_integration(
                child, "XO-001",
            )
            child.require_committed()
            self._integration_state(document, integrated)
        child = _ChildTransactionDocument(
            document, "Analyse crossover chair positions XO-001",
        )
        module.analyse_entity_chair_positions(
            child, "crossover", "XO-001",
            settings=old["chair_analysis_settings"],
        )
        child.require_committed()
        current = self._source(document)
        _require(current["p_identities"] == source["p_identities"],
                 "recalculation changed the qualified P identities")
        _require(all(current["config"].get(field) == old[field]
                     for field in _DEPENDENT_SETTINGS),
                 "recalculation changed canonical dependent settings")
        _require(self._canonical_metadata(current["config"])
                 == source["metadata"],
                 "recalculation changed canonical edit metadata")
        integration = self._integration_state(document, current["config"])
        _require((integration is not None)
                 == (source["integration"] is not None),
                 "recalculation changed the integration intent")

    def _report_object(self, document, name, role):
        module = self.module
        obj = document.getObject(name)
        _require(obj is not None
                 and module.object_string_property(obj, "GeneratedBy", "")
                 == module.GENERATOR_ID
                 and module.object_string_property(obj, "TemplateSetID", "")
                 == "SET-001"
                 and module.object_string_property(obj, "GeneratedRole", "")
                 == role, "a prepared report object identity changed")
        return obj

    def _prepare_reports(self, document, pending):
        """Materialise both derived reports before Generate's real commit."""
        module = self.module
        settings = module.settings_for_template_set(document, "SET-001")
        _require(settings is not None, "report source settings are missing")
        index = module.read_production_record_index(settings)
        _require(isinstance(index, dict)
                 and isinstance(index.get("records"), list),
                 "the final report source index is invalid")
        export_config = pending["request"]["production_export_config"]
        schedule_rows = self.originals[HOOK_NAMES[5]](
            index, export_config, "SET-001",
        )
        child = _ChildTransactionDocument(
            document, "Update Version {} production schedule".format(
                module.MACRO_VERSION_NUMBER,
            ),
        )
        schedule = self.originals[HOOK_NAMES[6]](
            child, "SET-001", schedule_rows,
        )
        child.require_committed()
        self._report_object(
            document, str(schedule.Name), module.PRODUCTION_SCHEDULE_ROLE,
        )
        material_config = module.read_material_report_config(settings)
        material_rows, diagnostics = self.originals[HOOK_NAMES[7]](
            document, index, settings, material_config, "SET-001",
        )
        child = _ChildTransactionDocument(
            document, "Update Version {} material report".format(
                module.MACRO_VERSION_NUMBER,
            ),
        )
        material = self.originals[HOOK_NAMES[8]](
            child, "SET-001", material_rows, material_config, diagnostics,
        )
        child.require_committed()
        self._report_object(
            document, str(material.Name), module.MATERIAL_REPORT_ROLE,
        )
        # Retain detached results only. The inherited postcommit callbacks
        # consume them without creating additional document transactions.
        pending["reports"] = copy.deepcopy({
            "index": index, "settings_name": str(settings.Name),
            "export_config": export_config, "schedule_rows": schedule_rows,
            "schedule_name": str(schedule.Name),
            "material_config": material_config,
            "material_rows": material_rows, "diagnostics": diagnostics,
            "material_name": str(material.Name), "stage": 0,
        })

    def _report_request(self, token, stage, document=None):
        pending = self._caller_request(token)
        if pending is None or pending["reports"] is None:
            return None
        _require(pending["finalised"]
                 and pending["reports"]["stage"] == stage,
                 "the inherited report callback order changed")
        current = self.module.App.ActiveDocument
        _require(current is not None
                 and id(current) == pending["document_id"]
                 and (document is None or id(document) == id(current)),
                 "the prepared report document changed")
        reports = pending["reports"]
        settings = current.getObject(reports["settings_name"])
        _require(settings is not None
                 and self.module.read_production_record_index(settings)
                 == reports["index"],
                 "the prepared report source index changed")
        return reports

    def _schedule_rows(self, index_payload, export_config, set_id):
        reports = self._report_request(self._invocation(), 0)
        if reports is None:
            return self.originals[HOOK_NAMES[5]](
                index_payload, export_config, set_id,
            )
        _require(set_id == "SET-001"
                 and export_config == reports["export_config"],
                 "the prepared production schedule request changed")
        reports["stage"] = 1
        return copy.deepcopy(reports["schedule_rows"])

    def _schedule(self, doc, set_id, rows):
        reports = self._report_request(self._invocation(), 1, doc)
        if reports is None:
            return self.originals[HOOK_NAMES[6]](doc, set_id, rows)
        _require(set_id == "SET-001" and rows == reports["schedule_rows"],
                 "the prepared production schedule rows changed")
        obj = self._report_object(
            doc, reports["schedule_name"], self.module.PRODUCTION_SCHEDULE_ROLE,
        )
        reports["stage"] = 2
        return obj

    def _material_rows(self, doc, index_payload, settings, config, set_id):
        reports = self._report_request(self._invocation(), 2, doc)
        if reports is None:
            return self.originals[HOOK_NAMES[7]](
                doc, index_payload, settings, config, set_id,
            )
        _require(set_id == "SET-001" and settings is not None
                 and str(settings.Name) == reports["settings_name"]
                 and str(settings.Document.Name) == str(doc.Name)
                 and config == reports["material_config"],
                 "the prepared material report request changed")
        reports["stage"] = 3
        return (copy.deepcopy(reports["material_rows"]),
                copy.deepcopy(reports["diagnostics"]))

    def _material(self, doc, set_id, rows, config, diagnostics=None):
        reports = self._report_request(self._invocation(), 3, doc)
        if reports is None:
            return self.originals[HOOK_NAMES[8]](
                doc, set_id, rows, config, diagnostics,
            )
        _require(set_id == "SET-001" and rows == reports["material_rows"]
                 and config == reports["material_config"]
                 and diagnostics == reports["diagnostics"],
                 "the prepared material report contents changed")
        obj = self._report_object(
            doc, reports["material_name"], self.module.MATERIAL_REPORT_ROLE,
        )
        reports["stage"] = 4
        return obj

    def _recompute(self, document, *args, **kwargs):
        pending = self._caller_request(self._invocation())
        if (pending is not None and pending["source"] is not None
                and not pending["finalised"]):
            _require(id(document) == pending["document_id"]
                     and pending["removed"] and pending["stored"]
                     and not pending["finalising"],
                     "the dependent finalisation boundary changed")
            pending["finalising"] = True
            try:
                self._rebuild(document, pending)
                self._prepare_reports(document, pending)
            except Exception:
                # The inherited Generate caller owns the real abort.
                pending["source"] = None
                pending["reports"] = None
                raise
            finally:
                pending["finalising"] = False
            pending["finalised"] = True
            pending["source"] = None
        elif pending is not None and pending["reports"] is not None:
            _require(pending["finalised"]
                     and pending["reports"]["stage"] == 4,
                     "the inherited reports did not complete exactly once")
            pending["reports"] = None
        return self.originals[HOOK_NAMES[4]](document, *args, **kwargs)
