"""Validate and report an embedded Phase 3 routed GUI oracle result."""

import json


if not isinstance(globals().get("TRACKTEMPLATE_WORKFLOW_RESULT"), dict):
    raise RuntimeError("The embedded Phase 3 workflow returned no result mapping.")
if module is not _PHASE3_SESSION.module:
    raise RuntimeError("The workflow driver did not use the routed B16 module.")
if (
    not _PHASE3_PRODUCT_COMPOSITION
    and _PHASE3_SESSION.active_route != _PHASE3_ROUTE
):
    raise RuntimeError("The active transition route changed during the workflow.")

_PHASE3_BINDINGS_AFTER = {
    name: _PHASE3_SESSION.module.__dict__[name]
    for name in _PHASE3_ROUTING["function_names"]
}
_PHASE3_CHANGED_BINDINGS = sorted(
    name
    for name in _PHASE3_BINDINGS_BEFORE
    if _PHASE3_BINDINGS_AFTER[name] is not _PHASE3_BINDINGS_BEFORE[name]
)
if _PHASE3_CHANGED_BINDINGS:
    raise RuntimeError(
        "The workflow changed routed transition bindings: {}.".format(
            ", ".join(_PHASE3_CHANGED_BINDINGS)
        )
    )

if _PHASE3_PRODUCT_COMPOSITION:
    _PHASE3_REVALIDATED_ROUTING = _PHASE3_SESSION.routing_record()
    _PHASE3_ACTIVE_ROUTE_AFTER = "modular"
else:
    _PHASE3_REVALIDATED_ROUTING = _PHASE3_SESSION.apply_route(_PHASE3_ROUTE)
    _PHASE3_ACTIVE_ROUTE_AFTER = _PHASE3_SESSION.active_route
if _PHASE3_REVALIDATED_ROUTING != _PHASE3_ROUTING:
    raise RuntimeError("The transition route record drifted after the workflow.")

_PHASE3_WORKFLOW_REPORT = {
    "schema_version": 1,
    "development_checkpoint": str(_PHASE3_API.DEVELOPMENT_CHECKPOINT),
    "matched_profile_id": str(
        _PHASE3_QUALIFICATION["compatibility_evaluation"][
            "matched_profile_id"
        ]
    ),
    "routing": _PHASE3_ROUTING,
    "active_route_after_workflow": _PHASE3_ACTIVE_ROUTE_AFTER,
    "workflow_module": _PHASE3_WORKFLOW_MODULE_NAME,
    "workflow_version": str(_PHASE3_SESSION.module.MACRO_VERSION_NUMBER),
    "launcher_sha256": _PHASE3_LAUNCHER_SHA256,
    "binding_records_before": _PHASE3_BINDING_RECORDS_BEFORE,
    "binding_identity_preserved": not _PHASE3_CHANGED_BINDINGS,
    "recipe": TRACKTEMPLATE_WORKFLOW_RESULT,
}
print(json.dumps(_PHASE3_WORKFLOW_REPORT, sort_keys=True))
