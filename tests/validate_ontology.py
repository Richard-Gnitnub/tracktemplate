#!/usr/bin/env python3
"""Validate the paired TrackTemplate product-system ontology."""

import json
import pathlib
import re
import sys
from urllib.parse import unquote


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.application.chair_definition import (  # noqa: E402
    CHAIR_CLASSIFICATIONS,
    CHAIR_PERMISSION_STATUSES,
    CHAIR_PROJECT_STATUSES,
)


ONTOLOGY_PATH = ROOT / "reference" / "ontology" / "tracktemplate.jsonld"
DOCUMENT_PATH = ROOT / "reference" / "ONTOLOGY.md"
CHAIR_SCHEMA_PATH = (
    ROOT / "reference" / "schemas" / "chair-definition-v1.schema.json"
)
MANIFEST_SCHEMA_PATH = (
    ROOT / "reference" / "schemas" / "dependency-manifest-v1.schema.json"
)

ONTOLOGY_ID = (
    "https://github.com/Richard-Gnitnub/tracktemplate/ontology"
)
TERM_NAMESPACE = ONTOLOGY_ID + "#"
ONTOLOGY_VERSION = "0.1.0"

EXPECTED_CONTEXT = {
    "dcterms": "http://purl.org/dc/terms/",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "tt": TERM_NAMESPACE,
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}

EXPECTED_CLASSES = {
    "tt:Adapter",
    "tt:Alignment",
    "tt:AlignmentElement",
    "tt:AnalyseOperation",
    "tt:AnalysisResult",
    "tt:CanonicalState",
    "tt:ChairAssignment",
    "tt:ChairComponent",
    "tt:ChairDefinition",
    "tt:ChairDefinitionPackage",
    "tt:CircularAlignmentElement",
    "tt:CompatibilityAdapter",
    "tt:Configuration",
    "tt:ControlledStatus",
    "tt:CoordinateFrame",
    "tt:Crossover",
    "tt:Datum",
    "tt:Dependency",
    "tt:DependencyManifest",
    "tt:DerivedArtifact",
    "tt:EditOperation",
    "tt:Evidence",
    "tt:ExactGeometry",
    "tt:ExactGeometryAdapter",
    "tt:ExportAdapter",
    "tt:ExportArtifact",
    "tt:ExportManifest",
    "tt:ExportOperation",
    "tt:InputSignature",
    "tt:ManifestBearingRecord",
    "tt:ManufacturingProfile",
    "tt:PermissionSet",
    "tt:PermissionBearingRecord",
    "tt:PermissionStatus",
    "tt:PersistenceAdapter",
    "tt:PersistentRecord",
    "tt:PlainLineTrack",
    "tt:PreviewScene",
    "tt:PresentationAdapter",
    "tt:ProceduralRule",
    "tt:ProductionIntent",
    "tt:ProjectStatus",
    "tt:ProjectStatusBearingRecord",
    "tt:ProvenanceClassification",
    "tt:ProvenanceRecord",
    "tt:Quantity",
    "tt:Rail",
    "tt:RailInterface",
    "tt:RailwayEntity",
    "tt:RailwayModel",
    "tt:ResultIntegritySignature",
    "tt:Route",
    "tt:Signature",
    "tt:SpecialTrackwork",
    "tt:StableIdentity",
    "tt:StraightAlignmentElement",
    "tt:Timber",
    "tt:ToleranceProfile",
    "tt:TopologyRelation",
    "tt:Track",
    "tt:TrackSupport",
    "tt:TransitionAlignmentElement",
    "tt:Turnout",
    "tt:Unit",
    "tt:ValidateOperation",
    "tt:ValidationResult",
    "tt:VersionedRecord",
    "tt:WorkflowOperation",
}

OBJECT_PROPERTY_SPECS = {
    "tt:classifiedAs": (
        "tt:ProvenanceRecord",
        "tt:ProvenanceClassification",
    ),
    "tt:consumes": ("tt:WorkflowOperation", "tt:CanonicalState"),
    "tt:containsEntity": ("tt:RailwayModel", "tt:RailwayEntity"),
    "tt:containsTrack": ("tt:RailwayModel", "tt:Track"),
    "tt:derivedFrom": ("tt:DerivedArtifact", "tt:CanonicalState"),
    "tt:describedByManifest": (
        "tt:ExportArtifact",
        "tt:ExportManifest",
    ),
    "tt:hasAlignment": ("tt:Track", "tt:Alignment"),
    "tt:hasAlignmentElement": (
        "tt:Alignment",
        "tt:AlignmentElement",
    ),
    "tt:hasChairAssignment": (
        "tt:RailwayModel",
        "tt:ChairAssignment",
    ),
    "tt:hasComponent": ("tt:ChairDefinition", "tt:ChairComponent"),
    "tt:hasConfiguration": ("tt:RailwayModel", "tt:Configuration"),
    "tt:hasDatum": ("tt:ChairDefinition", "tt:Datum"),
    "tt:hasDependencyManifest": (
        "tt:ManifestBearingRecord",
        "tt:DependencyManifest",
    ),
    "tt:hasManufacturingProfile": (
        "tt:ChairDefinitionPackage",
        "tt:ManufacturingProfile",
    ),
    "tt:hasPermissionSet": (
        "tt:PermissionBearingRecord",
        "tt:PermissionSet",
    ),
    "tt:hasPermissionStatus": (
        "tt:PermissionSet",
        "tt:PermissionStatus",
    ),
    "tt:hasProceduralRule": (
        "tt:ChairDefinition",
        "tt:ProceduralRule",
    ),
    "tt:hasProductionIntent": (
        "tt:RailwayModel",
        "tt:ProductionIntent",
    ),
    "tt:hasProjectStatus": (
        "tt:ProjectStatusBearingRecord",
        "tt:ProjectStatus",
    ),
    "tt:hasProvenance": (
        "tt:CanonicalState",
        "tt:ProvenanceRecord",
    ),
    "tt:hasQuantity": ("tt:ChairDefinition", "tt:Quantity"),
    "tt:hasRailInterface": (
        "tt:ChairDefinition",
        "tt:RailInterface",
    ),
    "tt:hasResultIntegritySignature": (
        "tt:AnalysisResult",
        "tt:ResultIntegritySignature",
    ),
    "tt:hasStableIdentity": (
        "tt:RailwayEntity",
        "tt:StableIdentity",
    ),
    "tt:hasTopologyRelation": (
        "tt:RailwayModel",
        "tt:TopologyRelation",
    ),
    "tt:invalidatedBy": ("tt:DerivedArtifact", "tt:EditOperation"),
    "tt:packagesChairDefinition": (
        "tt:ChairDefinitionPackage",
        "tt:ChairDefinition",
    ),
    "tt:persistsCanonicalState": (
        "tt:PersistentRecord",
        "tt:CanonicalState",
    ),
    "tt:produces": ("tt:WorkflowOperation", "tt:DerivedArtifact"),
    "tt:protectedBySignature": (
        "tt:DerivedArtifact",
        "tt:InputSignature",
    ),
    "tt:recordsDependency": (
        "tt:DependencyManifest",
        "tt:Dependency",
    ),
    "tt:requiresCurrentValidation": (
        "tt:ExportOperation",
        "tt:ValidationResult",
    ),
    "tt:supportedBy": ("tt:RailwayEntity", "tt:TrackSupport"),
    "tt:supportedByEvidence": (
        "tt:ProvenanceRecord",
        "tt:Evidence",
    ),
    "tt:usesChairDefinition": (
        "tt:ChairAssignment",
        "tt:ChairDefinition",
    ),
    "tt:usesRail": ("tt:RailwayEntity", "tt:Rail"),
    "tt:validatedBy": ("tt:ExportArtifact", "tt:ValidationResult"),
}

DATATYPE_PROPERTY_SPECS = {
    "tt:classificationCode": (
        "tt:ProvenanceClassification",
        "xsd:string",
    ),
    "tt:frameIdentifier": ("tt:CoordinateFrame", "xsd:string"),
    "tt:identifierValue": ("tt:StableIdentity", "xsd:string"),
    "tt:schemaIdentifier": ("tt:VersionedRecord", "xsd:string"),
    "tt:schemaVersion": (
        "tt:VersionedRecord",
        "xsd:nonNegativeInteger",
    ),
    "tt:signatureValue": ("tt:Signature", "xsd:string"),
    "tt:statusCode": ("tt:ControlledStatus", "xsd:string"),
    "tt:unitSymbol": ("tt:Unit", "xsd:string"),
}

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
TERM_RE = re.compile(r"`(tt:[A-Za-z0-9-]+)`")


def require(condition, message):
    """Raise an assertion with a stable diagnostic when a check fails."""
    if not condition:
        raise AssertionError(message)


def load_json(path):
    """Load strict JSON, rejecting duplicate object fields."""

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            require(
                key not in result,
                "duplicate JSON field in {}".format(path),
            )
            result[key] = value
        return result

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=unique_object,
        parse_constant=lambda value: require(
            False,
            "non-standard JSON number {!r} in {}".format(value, path),
        ),
    )


def value_id(value):
    """Return the identifier from one JSON-LD identifier object."""
    require(isinstance(value, dict), "expected a JSON-LD identifier object")
    identifier = value.get("@id")
    require(
        isinstance(identifier, str) and identifier,
        "JSON-LD identifier object lacks @id",
    )
    return identifier


def optional_value_id(value):
    """Return an identifier when a value is an identifier object."""
    if not isinstance(value, dict):
        return None
    identifier = value.get("@id")
    return identifier if isinstance(identifier, str) else None


def all_identifier_references(value):
    """Yield every JSON-LD identifier nested beneath a value."""
    if isinstance(value, dict):
        identifier = value.get("@id")
        if isinstance(identifier, str):
            yield identifier
        for key, child in value.items():
            if key != "@id":
                yield from all_identifier_references(child)
    elif isinstance(value, list):
        for child in value:
            yield from all_identifier_references(child)


def node_values(node, key):
    """Return a property value as a list without changing its content."""
    value = node.get(key, [])
    return value if isinstance(value, list) else [value]


def restrictions(node):
    """Return OWL restrictions declared as direct superclass expressions."""
    return [
        value
        for value in node_values(node, "rdfs:subClassOf")
        if isinstance(value, dict)
        and value.get("@type") == "owl:Restriction"
    ]


def require_some_restriction(nodes, class_id, property_id, target_id):
    """Require one some-values-from restriction on a class."""
    for restriction in restrictions(nodes[class_id]):
        if (
            optional_value_id(restriction.get("owl:onProperty"))
            == property_id
            and optional_value_id(restriction.get("owl:someValuesFrom"))
            == target_id
        ):
            return
    raise AssertionError(
        "{} lacks {} some {}".format(class_id, property_id, target_id)
    )


def require_exact_restriction(nodes, class_id, property_id, target_id):
    """Require one qualified-cardinality-one restriction on a class."""
    for restriction in restrictions(nodes[class_id]):
        cardinality = restriction.get("owl:qualifiedCardinality")
        if (
            optional_value_id(restriction.get("owl:onProperty"))
            == property_id
            and optional_value_id(restriction.get("owl:onClass"))
            == target_id
            and isinstance(cardinality, dict)
            and cardinality.get("@type") == "xsd:nonNegativeInteger"
            and cardinality.get("@value") == "1"
        ):
            return
    raise AssertionError(
        "{} lacks exactly one {} {}".format(
            class_id,
            property_id,
            target_id,
        )
    )


def enum_sets(value):
    """Yield every enum set nested in a JSON-compatible value."""
    if isinstance(value, dict):
        enum = value.get("enum")
        if isinstance(enum, list) and all(
            isinstance(item, str) for item in enum
        ):
            yield frozenset(enum)
        for child in value.values():
            yield from enum_sets(child)
    elif isinstance(value, list):
        for child in value:
            yield from enum_sets(child)


def controlled_codes(nodes, class_id, property_name):
    """Return codes from all individuals of a controlled class."""
    values = []
    for node in nodes.values():
        if node.get("@type") == class_id:
            code = node.get(property_name)
            require(
                isinstance(code, str) and code,
                "{} individual lacks {}".format(class_id, property_name),
            )
            values.append(code)
    require(
        len(values) == len(set(values)),
        "{} contains duplicate controlled codes".format(class_id),
    )
    return set(values)


def markdown_target(document, raw_target):
    """Resolve one repository-local Markdown link target."""
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1:target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    if (
        not target
        or target.startswith("#")
        or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target)
        or target.startswith("//")
    ):
        return None
    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    require(
        not target.startswith("/"),
        "absolute Markdown link in {}".format(document),
    )
    resolved = (document.parent / target).resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError as error:
        raise AssertionError(
            "repository-external Markdown link: {}".format(target)
        ) from error
    return resolved


def validate_document(document_text, graph_ids):
    """Validate the human reference and its formal-term coverage."""
    documented_terms = set(TERM_RE.findall(document_text))
    local_graph_ids = {
        identifier for identifier in graph_ids if identifier.startswith("tt:")
    }
    require(
        documented_terms == local_graph_ids,
        "human/formal term mismatch: undocumented {!r}; unknown {!r}".format(
            sorted(local_graph_ids - documented_terms),
            sorted(documented_terms - local_graph_ids),
        ),
    )
    require(
        "PROJECT_PLAN.md" in document_text,
        "ontology does not route live status to PROJECT_PLAN.md",
    )
    require(
        "supporting semantic reference" in document_text,
        "ontology responsibility classification is missing",
    )
    require(
        "ordinary track" not in document_text.lower(),
        "ontology introduces prohibited successor terminology",
    )
    for raw_target in MARKDOWN_LINK_RE.findall(document_text):
        target = markdown_target(DOCUMENT_PATH, raw_target)
        require(
            target is None or target.exists(),
            "broken ontology Markdown link: {}".format(raw_target),
        )


def validate_semantics(nodes):
    """Validate the load-bearing OWL relationships and restrictions."""
    require(
        value_id(nodes["tt:CanonicalState"]["owl:disjointWith"])
        == "tt:DerivedArtifact",
        "canonical and derived state are not declared disjoint",
    )
    require(
        value_id(nodes["tt:PreviewScene"]["owl:disjointWith"])
        == "tt:ValidationResult",
        "preview and validation result are not declared disjoint",
    )

    for property_id, target_id in (
        ("tt:derivedFrom", "tt:CanonicalState"),
        ("tt:protectedBySignature", "tt:InputSignature"),
    ):
        require_some_restriction(
            nodes,
            "tt:DerivedArtifact",
            property_id,
            target_id,
        )
    for property_id, target_id in (
        ("tt:validatedBy", "tt:ValidationResult"),
        ("tt:describedByManifest", "tt:ExportManifest"),
    ):
        require_some_restriction(
            nodes,
            "tt:ExportArtifact",
            property_id,
            target_id,
        )
    require_some_restriction(
        nodes,
        "tt:AnalysisResult",
        "tt:hasResultIntegritySignature",
        "tt:ResultIntegritySignature",
    )
    require_some_restriction(
        nodes,
        "tt:ExportOperation",
        "tt:requiresCurrentValidation",
        "tt:ValidationResult",
    )
    require_some_restriction(
        nodes,
        "tt:PersistentRecord",
        "tt:persistsCanonicalState",
        "tt:CanonicalState",
    )
    require_some_restriction(
        nodes,
        "tt:ChairDefinitionPackage",
        "tt:hasProvenance",
        "tt:ProvenanceRecord",
    )
    for property_id, target_id in (
        ("tt:packagesChairDefinition", "tt:ChairDefinition"),
        ("tt:hasDependencyManifest", "tt:DependencyManifest"),
    ):
        require_exact_restriction(
            nodes,
            "tt:ChairDefinitionPackage",
            property_id,
            target_id,
        )
    for property_id, target_id in (
        ("tt:hasComponent", "tt:ChairComponent"),
        ("tt:hasDatum", "tt:Datum"),
        ("tt:hasRailInterface", "tt:RailInterface"),
    ):
        require_some_restriction(
            nodes,
            "tt:ChairDefinition",
            property_id,
            target_id,
        )


def validate_controlled_codes(nodes):
    """Keep ontology individuals synchronized with executable schemas."""
    chair_schema = load_json(CHAIR_SCHEMA_PATH)
    manifest_schema = load_json(MANIFEST_SCHEMA_PATH)
    schema_enums = set(enum_sets(chair_schema))
    schema_enums.update(enum_sets(manifest_schema))

    expected_groups = (
        frozenset(CHAIR_CLASSIFICATIONS),
        frozenset(CHAIR_PERMISSION_STATUSES),
        frozenset(CHAIR_PROJECT_STATUSES),
    )
    for expected in expected_groups:
        require(
            expected in schema_enums,
            (
                "controlled code set is absent from versioned schemas: "
                "{!r}".format(sorted(expected))
            ),
        )

    require(
        controlled_codes(
            nodes,
            "tt:ProvenanceClassification",
            "tt:classificationCode",
        )
        == set(CHAIR_CLASSIFICATIONS),
        "ontology provenance classifications drifted",
    )
    require(
        controlled_codes(
            nodes,
            "tt:PermissionStatus",
            "tt:statusCode",
        )
        == set(CHAIR_PERMISSION_STATUSES),
        "ontology permission statuses drifted",
    )
    require(
        controlled_codes(
            nodes,
            "tt:ProjectStatus",
            "tt:statusCode",
        )
        == set(CHAIR_PROJECT_STATUSES),
        "ontology project statuses drifted",
    )


def main():
    """Validate both ontology representations and their authorities."""
    document = load_json(ONTOLOGY_PATH)
    require(document.get("@context") == EXPECTED_CONTEXT, "context drifted")
    graph = document.get("@graph")
    require(isinstance(graph, list) and graph, "ontology graph is empty")

    identifiers = [
        node.get("@id") for node in graph if isinstance(node, dict)
    ]
    require(
        all(
            isinstance(identifier, str) and identifier
            for identifier in identifiers
        ),
        "every ontology node must have a non-empty @id",
    )
    require(
        len(identifiers) == len(graph),
        "ontology graph contains a non-object node",
    )
    require(
        len(identifiers) == len(set(identifiers)),
        "ontology graph contains duplicate node identifiers",
    )
    nodes = {node["@id"]: node for node in graph}

    ontology = nodes.get(ONTOLOGY_ID)
    require(ontology is not None, "ontology header identity drifted")
    require(ontology.get("@type") == "owl:Ontology", "header type drifted")
    require(
        ontology.get("owl:versionInfo") == ONTOLOGY_VERSION,
        "ontology version drifted",
    )
    require(
        value_id(ontology.get("owl:versionIRI"))
        == ONTOLOGY_ID + "/" + ONTOLOGY_VERSION,
        "ontology version IRI drifted",
    )

    class_ids = {
        node["@id"] for node in graph if node.get("@type") == "owl:Class"
    }
    require(
        class_ids == EXPECTED_CLASSES,
        "class set drifted: missing {!r}; unexpected {!r}".format(
            sorted(EXPECTED_CLASSES - class_ids),
            sorted(class_ids - EXPECTED_CLASSES),
        ),
    )
    for class_id in class_ids:
        node = nodes[class_id]
        require(
            isinstance(node.get("rdfs:label"), str)
            and node["rdfs:label"].strip(),
            "{} lacks a label".format(class_id),
        )
        require(
            isinstance(node.get("rdfs:comment"), str)
            and node["rdfs:comment"].strip(),
            "{} lacks a bounded definition".format(class_id),
        )

    object_property_ids = {
        node["@id"]
        for node in graph
        if node.get("@type") == "owl:ObjectProperty"
    }
    require(
        object_property_ids == set(OBJECT_PROPERTY_SPECS),
        "object-property set drifted",
    )
    datatype_property_ids = {
        node["@id"]
        for node in graph
        if node.get("@type") == "owl:DatatypeProperty"
    }
    require(
        datatype_property_ids == set(DATATYPE_PROPERTY_SPECS),
        "datatype-property set drifted",
    )

    for specifications in (
        OBJECT_PROPERTY_SPECS,
        DATATYPE_PROPERTY_SPECS,
    ):
        for property_id, (domain_id, range_id) in specifications.items():
            node = nodes[property_id]
            require(
                value_id(node.get("rdfs:domain")) == domain_id,
                "{} domain drifted".format(property_id),
            )
            require(
                value_id(node.get("rdfs:range")) == range_id,
                "{} range drifted".format(property_id),
            )
            require(
                isinstance(node.get("rdfs:label"), str)
                and node["rdfs:label"].strip(),
                "{} lacks a label".format(property_id),
            )
            require(
                isinstance(node.get("rdfs:comment"), str)
                and node["rdfs:comment"].strip(),
                "{} lacks a definition".format(property_id),
            )

    graph_ids = set(identifiers)
    unresolved = {
        identifier
        for identifier in all_identifier_references(graph)
        if identifier.startswith("tt:") and identifier not in graph_ids
    }
    require(
        not unresolved,
        "ontology contains unresolved local identifiers: {!r}".format(
            sorted(unresolved)
        ),
    )

    validate_semantics(nodes)
    validate_controlled_codes(nodes)
    validate_document(
        DOCUMENT_PATH.read_text(encoding="utf-8"),
        graph_ids,
    )
    print("TrackTemplate product-system ontology validation passed")


if __name__ == "__main__":
    main()
