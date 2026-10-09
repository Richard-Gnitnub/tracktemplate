#!/usr/bin/env python3
"""Validate the owner-accepted, deliberately blocked Phase 1 S1 pilot plan."""

import copy
import hashlib
import json
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import validate_dependency_manifest as manifest_validator  # noqa: E402
from governance_markdown import direct_section_content  # noqa: E402


PLAN_PATH = (
    ROOT / "reference" / "phase-evidence" / "S1_PILOT_PLAN.md"
)
MANIFEST_PATH = (
    ROOT / "reference" / "manifests" / "s1-chair-pilot.dependency-manifest.json"
)
LINEAGE_PATH = ROOT / "reference" / "lineage" / "phase1-s1-core-lineage.json"
ORACLE_PATH = ROOT / "reference" / "oracles" / "templot5-556b-s1-oracle.json"
SOURCE_EXPECTATIONS = {
    "AdvancedTurnout.FCMacro": (
        "10.2A8A7B14",
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088",
    ),
    (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ): (
        "10.2A8A7B15",
        "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
    ),
}
DECISION_STATES = {
    "S1-01": "accepted-direction",
    "S1-02": "accepted-direction",
    "S1-03": "accepted-direction",
    "S1-04": "accepted-direction",
    "S1-05": "accepted-direction",
    "S1-06": "accepted-direction",
    "S1-07": "owner-decision-required",
    "S1-08": "owner-decision-required",
    "S1-09": "owner-decision-required",
    "S1-10": "owner-decision-required",
    "S1-11": "owner-decision-required",
    "S1-12": "blocked-evidence",
    "S1-13": "owner-decision-required",
    "S1-14": "blocked-evidence",
    "S1-15": "owner-decision-required",
}
INTENDED_USES = (
    "public-redistribution",
    "commercial-production",
    "publication",
    "physical-production",
)
REQUIRED_MARKERS = (
    "Status: **Accepted Phase 1 control; production definition and production "
    "pilot",
    "authoritative interchange is a neutral, versioned TrackTemplateMacro",
    "Serialised output-affecting numbers use exact decimal strings",
    "`+X` longitudinally along the nominal rail direction",
    "`+Y` from the gauge side towards the field side",
    "`+Z` upwards from the base mounting plane",
    "validate the complete package before creating geometry",
    "reject unsupported future schema versions",
    "leave the document and filesystem unchanged",
    "a precise prototype/company/standard designation",
    "A scan or CAD body may assist fitting, but cannot alone",
    "Phase 1 fixes the metric families, not unsupported numerical limits",
    "Mesh hash, face order, visual similarity or a low aggregate surface residual",
    "do not publish “LMS”, “REA” or another attribution by assumption",
    "Target CC0-1.0 only if the project controls the complete package rights",
    "The project owner explicitly accepted this plan on 2026-07-22",
    "> I accept S1_PILOT_PLAN.md as the blocked Phase 1 control, including S1-04",
    "> S1-15 remain blocked pending their stated evidence and decisions.",
    "no S1 production definition, project-cleared package or permission from a",
    "manifest cannot substitute for the recorded owner acceptance",
)
REFERENCE_CRITERIA_HEADING = (
    "S1 reference-comparison criteria under D-P9-007"
)
REFERENCE_CRITERIA_IDENTITIES = (
    "7d5a08b269b52e6ebbc26453853ce308343ccd54636454d589add2e1397cc2d6",
    "7444309a79f5940c7026b571871b118f70d0ce93578380ef89adcb187c723861",
    "9d3def6445bc0181ad971639110927c380a8b15d162e00d69ac5f017c6f98f18",
)
# Each row owns its rule; a matching phrase elsewhere is insufficient.
REFERENCE_CRITERIA = (
    ("Package identity, provenance and neutral round-trip", (
        "reference-only status must agree exactly",
        "No numerical tolerance applies",
        "reject unsigned corruption and schema 2 before native construction",
        "Prototype, model-fit and manufacturing records stay separate",
        "Production refusal stays",
    )),
    ("Units, scale and frame", (
        "Source decimal values and unit conversions stay exact",
        "Full-size lengths use mm and chair-local-right-handed-v1",
        "same origin and central-key placement",
        "381/5 = 76.2", "f, f^2 and f^3",
        "Algebraic coordinates keep their exact representation",
        "A0 rail already uses model mm and receives no second scale "
        "conversion",
        "display crop is not a canonical rail length",
    )),
    ("Source finite boundaries and sections", (
        "ordered face boundaries, diagonals and recorded coplanar "
        "consolidations must agree",
        "Rational coefficients must agree exactly",
        "Source facets and quantisation stay unchanged",
        "historical binary64 formulas and separately dimensioned limits",
        "120 digits", "130 digits for the outer jaw and 140 for the inner jaw",
        "1e-100 mm for each length field and 1e-100 mm^3 for each volume "
        "field",
        "coordinate, landmark, section, bounds and volume comparisons",
        "limits stay separate from the native epsilon guard",
        "They do not describe uncertainty in physical measurements",
    )),
    ("Native named-vertex distance and axis bounds", (
        "Each Euclidean named-vertex distance must be at most epsilon",
        "maximum absolute residual over the six bound coordinates must "
        "be at most epsilon",
        "applies separately in full-size mm and model mm",
        "does not become a physical-fit allowance after scaling",
    )),
    ("Kernel tolerance", (
        "at most 1e-7 mm",
        "math.isclose(value, 1e-7, rel_tol=1e-12, abs_tol=0)",
        "with values in mm",
        "permits no physical clearance or kernel-tolerance growth",
    )),
    ("Component and assembly volume", (
        "Each component volume must be positive and finite",
        "abs(Vnative - Vanalytic) <= max(Ashape * epsilon, "
        "abs(Vanalytic) * 1e-12)",
        "budget has units mm³",
        "preserve the component sum within the sum of the component budgets",
        "five solids stay separate and unfused",
        "component sum is not a fused material volume",
    )),
    ("Projection comparison", (
        "Coordinates and landmarks must use exact factor f",
        "Identities, face cycles and topology stay unchanged",
        "rel_tol=1e-12 and abs_tol=0",
        "Bmodel + Bfull * f^3", "epsilon * (1 + f)",
        "without acceptance of an arbitrary scale",
    )),
    ("Interface plane constraints", (
        "Analytical equation residuals must equal exact zero",
        "including signed changes below epsilon",
        "Euclidean distance at most epsilon",
        "epsilon * (abs(a) + abs(b) + abs(c))",
        "36 named-point checks, eight finite faces and one endpoint relation",
        "equation residual is not a surface distance",
    )),
    ("Finite rail contact and nonpenetration", (
        "Contact polygon identities, area-squared values in mm⁴, "
        "half-space signs and finite extents must agree exactly",
        "(Lchair + Lrail) * epsilon in mm²",
        "(Achair + Arail) * epsilon in mm³",
        "seat 1, inner jaw 4, key 7, base 0 and outer jaw 0",
        "All five rail common volumes must stay zero within that "
        "numerical budget",
        "do not establish physical fit",
    )),
    ("Under-head contact dimension", (
        "must stay an edge, with zero area and no face",
        "reference length stays in the local packet",
        "2 * Nedges * epsilon",
        "cannot convert an edge into a bearing area",
    )),
    ("Deliberate key/outer-jaw overlap", (
        "exact reference common volume must stay the product of the "
        "recorded footprint area and depth",
        "Those values stay in the local packet",
        "(Akey + Aouter) * epsilon in mm³",
        "Positive overlap stays mandatory for this reference",
        "overlap is not a fit allowance or proof of preload or retention",
    )),
    ("Remaining pairwise joints", (
        "All ten pair identities, distances and relation classes must agree",
        "base/key, seat/key, key/inner and outer/inner",
        "base/outer, base/inner, seat/outer and seat/inner",
        "Positive-overlap pairs are base/seat and key/outer",
        "Exact distances stay in the local packet",
        "absolute base/seat common volume stays a host observation only",
        "independently established base/seat overlap relation, not an "
        "independently derived absolute overlap magnitude",
    )),
    ("Topology and validity", (
        "Ordered component and face identities must agree exactly",
        "closed, valid and correctly oriented, with positive volumes",
        "five individual solids in one Compound",
        "exact vertex, edge and face counts in row 13 of the local packet",
        "no authority for healing, a fused chair or production export",
    )),
)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _table_cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _decision_rows(text, errors):
    start_marker = "## Decision register"
    finish_marker = "## Phase 1 acceptance boundary"
    start = text.find(start_marker)
    finish = text.find(finish_marker, start + len(start_marker))
    if start < 0 or finish < 0:
        errors.append("S1 decision-register boundary is missing")
        return []
    rows = []
    for line in text[start:finish].splitlines():
        if not line.startswith("|"):
            continue
        cells = _table_cells(line)
        if len(cells) != 5 or cells[0] in {"ID", "---"}:
            continue
        rows.append(cells)
    return rows


def _all_reviews_have_status(review, status):
    return (
        isinstance(review, dict)
        and set(review) == set(manifest_validator.NON_COPYRIGHT_AREAS)
        and all(item.get("status") == status for item in review.values())
    )



def _research_boundary_errors(text):
    """Keep current research scope separate from historical production gates."""
    section = direct_section_content(
        text, "Phase 9A research and Phase 9B production boundary",
    )
    flat = " ".join(section.replace("`", "").split())
    clauses = (
        "Independent primary production evidence is not necessary before "
        "this research implementation or architecture proof",
        "The neutral TrackTemplate schema stays canonical",
        "A Templot file, opaque mesh or retained generated body cannot "
        "become the canonical definition",
        "Every Templot-derived field must keep its exact source identity, "
        "source hash, source locator, derivation inputs and "
        "reference-only status",
        "A research input that affects geometry is an output-affecting "
        "dependency of the research output",
        "Research acceptance is not production admission",
        "outputs stay private-development and must not have "
        "project-cleared status",
        "They stay local and untracked without separate redistribution "
        "authority",
        "Do not identify Templot-derived values as independently "
        "evidenced prototype facts",
        "Prototype geometry, model rail-fit policy and manufacturing "
        "compensation stay separate",
        "S1-07 through S1-13 and S1-15 keep their production-evidence "
        "obligations",
        "Do not construct an affected component while its "
        "output-affecting fields are unresolved",
        "No missing dimension or numerical tolerance can receive an invented default",
        "The frozen Templot contract stays a different source of optional "
        "comparison evidence",
        "D-P9-005 removes the exact executable and output as mandatory "
        "acceptance evidence",
        "Phase 9B keeps the minimum production evidence bundle, package-rights, "
        "non-copyright-rights, dependency-manifest and release gates",
        "After an input change, each affected definition, geometry, pilot "
        "and output check of the final production package must give a "
        "PASS result",
        "The existing blocked production manifest, lineage and oracle "
        "records keep their current status",
    )
    return [
        "S1 research boundary drifted: " + clause
        for clause in clauses if clause not in flat
    ]


def _engineering_reference_errors(text):
    """Require engineering evidence without changing frozen oracle history."""
    section = direct_section_content(
        text, "Chair acceptance evidence under D-P9-005",
    )
    flat = " ".join(section.replace("`", "").split())
    clauses = (
        "For chair acceptance, an independent engineering reference chain "
        "is mandatory",
        "Record the source identity and applicable source location "
        "for each value",
        "Record units, uncertainty, derivation inputs and the intended use",
        "Before acceptance, explicit provenance and accepted numerical "
        "tolerances are mandatory for every production-affecting value",
        "Keep a separation between prototype geometry, model rail-fit "
        "policy and manufacturing compensation",
        "Missing evidence or a tolerance that is not accepted stays a finding",
        "Do not give a Templot-derived value independent status without "
        "supporting independent evidence",
        "Preserve its historical Templot lineage after independent "
        "confirmation or replacement",
        "Keep a separation between the rights conditions and engineering "
        "acceptance",
        "Agreement with Templot is not sufficient for acceptance of a chair "
        "value or tolerance",
        "They are not production requirements without independent "
        "engineering justification",
        "Record that justification and its acceptance before such a choice "
        "controls production",
        "Do not do more Phase 9 work on this host to operate 556b through "
        "Lazarus, Windows VM or Wine",
        "Keep the frozen capture contract, source identities, lineage, "
        "failed evidence and local files",
        "No different Templot executable becomes an exact-556b result",
        "An absent 556b capture does not stop chair acceptance by itself",
        "D-P9-005 supersedes the mandatory S1-14 comparison condition",
        "The register and frozen capture contract keep their historical "
        "identities and status",
        "That permission does not accept a definition, numerical tolerance, "
        "assisted S1 pilot, physical fit or production output",
        "Phase 9A stays Open at 1/4",
        "Exits 9A-1–3 stay Pending",
        "Phase 9B stays Not started at 0/6",
    )
    return [
        "S1 engineering reference boundary drifted: " + clause
        for clause in clauses if clause not in flat
    ]


def _exit1_acceptance_errors(text):
    """Keep the later research acceptance separate from production duties."""
    section = direct_section_content(
        text, "Bounded Exit 9A-1 acceptance under D-P9-006",
    )
    identities = (
        "49c72c294335898ba4e2f3cb02581c8ef6e539a7",
        "df5ae7d941754ed7c18ea450d1d22559c61efbd5baaa638d2e84fa9d96b8e4c7",
        "cf45882bbdfa645bd893a22ca0e7f9200810282a2aab015c98074e0c1aee941a",
    )
    errors = [
        "S1 Exit 9A-1 accepted identity drifted: " + identity
        for identity in identities if identity not in section
    ]
    flat = " ".join(section.replace("`", "").split())
    clauses = (
        "accepts only the named frozen five-component S1 ChairDefinition "
        "and Exit 9A-1 for reference-only architecture proof",
        "chair evidence condition only for this named S1 ChairDefinition "
        "and Exit 9A-1",
        "Independent production evidence is not necessary before this "
        "acceptance",
        "Independent engineering evidence, explicit provenance and "
        "accepted numerical tolerances remain mandatory for production "
        "under D-P9-005",
        "The D-P9-005 section above keeps the status at that historical "
        "decision",
        "The external decision identifies the package and manifest by "
        "these hashes",
        "package bytes and historical acceptance: not-accepted and "
        "validation: not-run metadata stay unchanged",
        "supersedes that historical acceptance only for the bounded "
        "9A-1 reference scope",
        "It does not accept a production package or rights claim",
        "same neutral ChairDefinition schema and procedural chair generator",
        "It does not give the L1 package new acceptance or use authority",
        "Construction guards and source agreement are not accepted "
        "reference tolerances or physical-fit tolerances",
        "No assisted S1 pilot, physical fit, preload, retention or "
        "manufacturing capability is accepted",
        "model rail-fit policy and manufacturing compensation keep "
        "separate provenance",
        "The 113-entry register, source printing allowances and unresolved "
        "production evidence keep their status",
        "D-P9-004 private-use conditions still apply",
        "Phase 9A is Open at 2/4",
        "Exits 9A-1 and 9A-4 are Evidenced and owner-accepted",
        "Exits 9A-2 and 9A-3 stay Pending",
        "Phase 9B stays Not started at 0/6",
        "No numerical tolerance, production output or positive rights "
        "finding follows",
    )
    errors.extend(
        "S1 Exit 9A-1 acceptance boundary drifted: " + clause
        for clause in clauses if clause not in flat
    )
    return errors


def _reference_criteria_errors(text):
    """Protect the scoped criteria without promoting pending acceptance."""
    section = direct_section_content(text, REFERENCE_CRITERIA_HEADING)
    flat = " ".join(section.replace("`", "").split())
    errors = [
        "S1 reference criteria identity drifted: " + identity
        for identity in REFERENCE_CRITERIA_IDENTITIES
        if identity not in section
    ]
    clauses = (
        "D-P9-007 supersedes only its statement that the specified "
        "construction guards are not accepted reference tolerances",
        "The physical-fit and production exclusions stay unchanged",
        "decision does not accept Exit 9A-2 or the assisted S1 pilot",
        "Phase 9A stays Open at 2/4",
        "Exits 9A-2 and 9A-3 stay Pending",
        "Phase 9B stays Not started at 0/6",
        "This decision accepts no other package, rail section, model scale "
        "or manufacturing profile",
        "Source coordinates, dimensions, distances and overlap magnitudes "
        "stay in that local packet and its identified evidence",
        "proposal to accept Exit 9A-2 in those earlier records has no "
        "acceptance authority",
        "epsilon = 1e-7 mm and f = 5/381",
        "A is an area in mm², V is a volume in mm³, and B is a volume "
        "budget in mm³",
        "L is the total B-rep edge length in mm, not the physical rail length",
        "Nedges is the number of edges in the compared contact",
        "For this exact frozen faceted reference, the comparison uses "
        "complete finite face and section correspondence. A separate "
        "surface-distance maximum and distribution are not necessary for "
        "this comparison",
        "not a new measured surface-distance distribution or Hausdorff result",
        "Source facets do not become smooth prototype surfaces",
        "D-P9-007 accepts no new geometry or numerical limit",
        "The 113-entry register, frozen package bytes, source allowances "
        "and field provenance stay unchanged",
        "acceptance: not-accepted and validation: not-run fields",
        "This external decision does not promote those fields or accept "
        "a phase exit",
        "Physical rail measurements, fit tolerances, preload, retention "
        "and manufacturing capability stay outside this decision",
        "Prototype identity, production rights, production output and "
        "the assisted S1 pilot also stay outside it",
        "This decision claims no measured whole-surface statistics or "
        "independently derived absolute base/seat overlap magnitude",
        "D-P9-004 private-use conditions and all other acceptance "
        "boundaries stay",
    )
    errors.extend(
        "S1 reference criteria boundary drifted: " + clause
        for clause in clauses if clause not in flat
    )
    if "#bounded-exit-9a-1-acceptance-under-d-p9-006" not in section:
        errors.append("S1 reference criteria lost frozen scope owner")
    rows = [_table_cells(line) for line in section.splitlines()
            if line.startswith("|")]
    expected_names = ["{}. {}".format(index, name)
                      for index, (name, _) in enumerate(REFERENCE_CRITERIA, 1)]
    if (len(rows) != 15 or any(len(row) != 3 for row in rows)
            or [row[0] for row in rows[2:]] != expected_names):
        errors.append("S1 reference criteria inventory or order drifted")
        return errors
    for row, (_name, required) in zip(rows[2:], REFERENCE_CRITERIA):
        content = " ".join(" ".join(row[1:]).replace("`", "").split())
        errors.extend(
            "S1 reference criterion {} drifted: {}".format(row[0], clause)
            for clause in required if clause not in content
        )
    return errors


def _exit2_acceptance_errors(text):
    """Keep exit admission separate from the historical criteria decision."""
    section = direct_section_content(
        text, "Bounded Exit 9A-2 acceptance under D-P9-008",
    )
    flat = " ".join(section.replace("`", "").split())
    clauses = (
        "accepts Exit 9A-2 only for the exact frozen five-component S1 "
        "reference",
        "package, manifest, A0 rail section and thirteen criteria "
        "identified above",
        "The criteria and their numerical limits stay unchanged",
        "The panel owns the accepted evidence and exclusions",
        "Phase 9A is Open at 3/4",
        "Exit 9A-3 stays Pending",
        "Phase 9B stays Not started at 0/6",
        "The D-P9-007 section records criteria-only acceptance at its date",
        "D-P9-008 gives acceptance for Exit 9A-2",
        "It changes no geometry, package bytes, historical metadata or "
        "entry in the 113-entry register",
        "It accepts no assisted S1 pilot, physical fit, manufacturing "
        "capability, production output or rights claim",
        "The authorised publication is a draft PR. Do not merge",
    )
    errors = [
        "S1 Exit 9A-2 boundary drifted: " + clause
        for clause in clauses if clause not in flat
    ]
    if ("../current/PHASE_EVIDENCE.md"
            "#phase-9a-exit-2-acceptance-panel") not in section:
        errors.append("S1 Exit 9A-2 decision owner link drifted")
    return errors


def _exit3_acceptance_errors(text):
    """Keep the seven pilot duties within the accepted research scope."""
    section = direct_section_content(
        text, "Bounded Exit 9A-3 acceptance under D-P9-009",
    )
    flat = " ".join(section.replace("`", "").split())
    clauses = (
        "accepts only the frozen reference-only assisted S1 pilot and "
        "Exit 9A-3",
        "The owner accepts its declared components, landmarks and "
        "retained findings under D-P9-007",
        "The accepted fitting method uses the same neutral ChairDefinition "
        "and procedural chair generator",
        "It does not use retained FreeCAD shapes as authoritative input",
        "D-P9-009 supplies the bounded assisted S1 pilot acceptance that "
        "D-P9-007 and D-P9-008 did not supply",
        "It applies the existing comparison method and numerical limits "
        "only to this exact frozen reference",
        "The general production and assisted-pilot duties below stay "
        "applicable outside this accepted scope",
        "No new numerical tolerance follows",
        "The package keeps acceptance: not-accepted and validation: not-run",
        "Geometry, source printing allowances, package bytes, the "
        "113-entry register and all production obligations stay unchanged",
        "Prototype geometry, model rail-fit policy and manufacturing "
        "compensation stay separate",
        "No physical fit, preload, retention, manufacturing capability, "
        "production package, output or rights acceptance follows",
        "Arbitrary automatic scan assimilation stays outside the RC "
        "qualification matrix",
        "Phase 9A is Open at 4/4",
        "All four Phase 9A exits are Evidenced and owner-accepted",
        "Phase 9A is not closed",
        "Phase 9B stays Not started at 0/6",
        "Publish only the validated draft PR. Do not merge or close Phase 9A",
    )
    errors = ["S1 Exit 9A-3 boundary drifted: " + clause
              for clause in clauses if clause not in flat]
    for target in (
        "../current/PHASE_EVIDENCE.md#phase-9a-exit-3-acceptance-panel",
        "#bounded-exit-9a-1-acceptance-under-d-p9-006",
        "#s1-reference-comparison-criteria-under-d-p9-007",
    ):
        if target not in section:
            errors.append("S1 Exit 9A-3 owner link drifted: " + target)
    duties = (
        ("Source and use basis", (
            "All 119 lineage records stay derived and reference-only",
            "D-P9-004 private-use conditions",
        )),
        ("Units, scale and frame", (
            "Source decimal values and unit conversions stay exact",
            "chair frame and its five datums stay explicit",
            "model scale is 1:76.2", "A0 rail already uses model mm",
            "source-coordinate calibration, not physical measurement "
            "calibration",
        )),
        ("Components and landmarks", (
            "base-plinth, rail-seat, inner-jaw, key and outer-jaw",
            "declared datums and source landmarks",
            "Fastenings and plug/socket components stay outside the scope",
        )),
        ("Parameters and findings", (
            "113 source quantities keep their derivations and unresolved "
            "physical measurement uncertainty",
            "A null uncertainty is not zero uncertainty",
            "No value becomes a measured physical dimension or an "
            "independently evidenced prototype fact",
        )),
        ("Procedural construction", (
            "chair_research.prepare_chair_assembly_research",
            "existing model and rail research paths",
            "Native validation, save/reopen and the nine FreeCAD views "
            "remain the evidence",
        )),
        ("Residual comparison", (
            "unchanged 13 D-P9-007 criteria apply only to this exact frozen "
            "assisted S1 pilot",
            "Complete finite face and section correspondence remains "
            "its reference comparison",
            "no measured whole-surface distribution or independently "
            "derived absolute base/seat overlap magnitude",
        )),
        ("Operator approval", (
            "current D-P9-009 owner instruction accepts this bounded "
            "assisted S1 pilot",
            "Earlier decisions and the earlier approval of reference views "
            "keep their historical limits",
            "This external decision leaves package metadata unchanged",
        )),
    )
    rows = [_table_cells(line) for line in section.splitlines()
            if line.startswith("|")]
    if (len(rows) != 9 or any(len(row) != 2 for row in rows)
            or [row[0] for row in rows[2:]] != [name for name, _ in duties]):
        errors.append("S1 Exit 9A-3 duty inventory or order drifted")
        return errors
    for row, (name, required) in zip(rows[2:], duties):
        content = " ".join(row[1].replace("`", "").split())
        errors.extend("S1 Exit 9A-3 duty drifted: " + name + ": " + clause
                      for clause in required if clause not in content)
    return errors


def validate_plan(
    text,
    manifest,
    lineage,
    oracle,
    check_repository=True,
):
    errors = (
        _research_boundary_errors(text)
        + _engineering_reference_errors(text)
        + _exit1_acceptance_errors(text)
        + _reference_criteria_errors(text)
        + _exit2_acceptance_errors(text)
        + _exit3_acceptance_errors(text)
    )
    for marker in REQUIRED_MARKERS:
        if marker not in text:
            errors.append("S1 pilot plan marker is missing: {}".format(marker))

    rows = _decision_rows(text, errors)
    row_ids = [row[0] for row in rows]
    if row_ids != list(DECISION_STATES):
        errors.append("S1 decision identities/order are invalid")
    if len(row_ids) != len(set(row_ids)):
        errors.append("S1 decision identities are duplicated")
    for row in rows:
        if not all(cell for cell in row):
            errors.append("S1 decision {} contains an empty cell".format(row[0]))
        expected_state = DECISION_STATES.get(row[0])
        if row[2] != expected_state:
            errors.append("S1 decision {} state is invalid".format(row[0]))

    if "Status: **Project-cleared" in text:
        errors.append("S1 pilot plan falsely claims project clearance")
    lowered_text = text.lower()
    if "full-size millimetres" not in lowered_text:
        errors.append("S1 plan does not state its recommended canonical length unit")
    if "original decimal value and unit" not in lowered_text:
        errors.append("S1 plan does not preserve source quantities")

    manifest_errors = manifest_validator.validate_document(manifest)
    if manifest_errors:
        errors.extend("S1 manifest: {}".format(item) for item in manifest_errors)
    strict_errors = manifest_validator.validate_document(
        manifest, require_project_cleared=True
    )
    if not any("rather than project-cleared" in item for item in strict_errors):
        errors.append("S1 manifest no longer fails the strict project-cleared gate")

    subject = manifest.get("subject") if isinstance(manifest, dict) else {}
    if not isinstance(subject, dict):
        subject = {}
    if subject.get("identifier") != "tracktemplate:s1-chair-pilot":
        errors.append("S1 manifest subject identity drifted")
    if subject.get("version") != "0-unresolved":
        errors.append("S1 manifest prematurely received a package version")
    if subject.get("package_license") != "NOASSERTION":
        errors.append("S1 manifest prematurely received a package licence")
    if tuple(manifest.get("intended_uses") or []) != INTENDED_USES:
        errors.append("S1 intended-use declaration drifted")
    project_status = manifest.get("project_status") or {}
    if project_status.get("status") != "unknown":
        errors.append(
            "S1 manifest must remain unknown before final package/evidence review"
        )
    if (
        project_status.get("reviewed_on") != "2026-07-22"
        or project_status.get("reviewed_by")
        != "Project owner and Phase 1 inventory"
        or project_status.get("decision_reference")
        != "reference/lineage/phase1-s1-core-lineage.json"
        or "Phase 1 control plan is accepted"
        not in project_status.get("reason", "")
        or "final package acceptance" not in project_status.get("reason", "")
    ):
        errors.append("S1 manifest does not preserve the accepted-plan boundary")
    if not _all_reviews_have_status(
        manifest.get("non_copyright_review"), "not-performed"
    ):
        errors.append("S1 package rights reviews were promoted without evidence")

    dependencies = manifest.get("dependencies")
    if not isinstance(dependencies, list):
        dependencies = []
    dependency_map = {
        item.get("identifier"): item
        for item in dependencies
        if isinstance(item, dict)
    }
    if set(dependency_map) != {
        "s1-primary-evidence-unselected",
        "templot5-556b-local-comparison",
    }:
        errors.append("S1 manifest dependency identity set drifted")
    primary = dependency_map.get("s1-primary-evidence-unselected", {})
    if (
        primary.get("role") != "production-input"
        or primary.get("output_affecting") is not True
        or primary.get("license_expression") != "NOASSERTION"
        or (primary.get("project_status") or {}).get("status") != "unknown"
        or set((primary.get("permissions") or {}).values()) != {"unknown"}
        or not _all_reviews_have_status(
            primary.get("non_copyright_review"), "not-performed"
        )
    ):
        errors.append("unselected primary S1 evidence is not fail-closed")
    comparison = dependency_map.get("templot5-556b-local-comparison", {})
    if (
        comparison.get("role") != "comparison-only"
        or comparison.get("output_affecting") is not False
        or (comparison.get("project_status") or {}).get("status")
        != "reference-only"
    ):
        errors.append("Templot S1 evidence escaped its comparison-only boundary")

    if lineage.get("status") != "blocked":
        errors.append("first-S1/core lineage register is not blocked")
    if tuple(lineage.get("intended_uses") or []) != INTENDED_USES:
        errors.append("S1 plan and lineage intended uses differ")
    scopes = lineage.get("scopes")
    if not isinstance(scopes, list) or not scopes:
        errors.append("first-S1/core lineage scopes are missing")
        scopes = []
    if any(scope.get("status") != "blocked" for scope in scopes):
        errors.append("an S1/core lineage scope was promoted without evidence")
    for scope in scopes:
        for entry in scope.get("entries") or []:
            if entry.get("current_project_status") == "project-cleared":
                errors.append("an S1/core lineage entry was prematurely cleared")

    if oracle.get("status") != "blocked":
        errors.append("Templot 556b S1 oracle is not blocked")
    if oracle.get("permitted_role") != "local comparison oracle only":
        errors.append("Templot 556b S1 oracle role drifted")
    blockers = oracle.get("blockers")
    if not isinstance(blockers, list) or len(blockers) != 4:
        errors.append("Templot 556b S1 blocker set drifted")
    elif any(item.get("status") != "open" for item in blockers):
        errors.append("Templot 556b S1 blocker closed without capture evidence")
    acceptance_gate = oracle.get("acceptance_gate") or {}
    if (
        acceptance_gate.get("status") != "blocked"
        or acceptance_gate.get("canonical_production_input") is not False
        or acceptance_gate.get("raw_hash_equality_is_geometry_oracle") is not False
    ):
        errors.append("Templot 556b S1 acceptance gate weakened")

    if check_repository:
        for relative_path, (version, expected_digest) in SOURCE_EXPECTATIONS.items():
            path = ROOT / relative_path
            if _sha256(path) != expected_digest:
                errors.append("{} source fingerprint changed".format(relative_path))
            if version not in path.read_text(encoding="utf-8"):
                errors.append("{} version token is missing".format(relative_path))
        chair_schema = (
            ROOT / "reference" / "schemas" / "chair-definition-v1.schema.json"
        )
        if chair_schema.exists():
            phase4_evidence = (
                ROOT
                / "reference"
                / "history"
                / "phase-closeouts"
                / "PHASE4_CLOSEOUT.md"
            ).read_text(encoding="utf-8")
            if "Phase 4 chair-definition package contract" not in phase4_evidence:
                errors.append(
                    "chair-definition schema is not attributed to its later "
                    "Phase 4 evidence and owner decision"
                )

    return errors


def _expect_invalid(text, manifest, lineage, oracle, label):
    errors = validate_plan(
        text,
        manifest,
        lineage,
        oracle,
        check_repository=False,
    )
    if not errors:
        raise AssertionError("mutation unexpectedly passed: {}".format(label))


def _validate_reference_criteria_mutations(text):
    """Reject authority widening and dimensionally wrong comparison rules."""
    section = direct_section_content(text, REFERENCE_CRITERIA_HEADING)
    mutations = []
    for identity in REFERENCE_CRITERIA_IDENTITIES:
        mutations.append((identity, "unreviewed-evidence", "identity"))
    for before, after in (
        ("Exits 9A-2 and 9A-3 stay Pending",
         "Exits 9A-2 and 9A-3 are accepted"),
        ("Phase 9A stays Open at 2/4", "Phase 9A stays Open at 3/4"),
        ("Phase 9B stays Not started at 0/6", "Phase 9B is Open at 0/6"),
        ("accepts no other package", "accepts any other package"),
        ("epsilon = 1e-7 mm", "epsilon = 1e-6 mm"),
        ("f = 5/381", "f = 1/76"),
        ("total B-rep edge length", "physical rail length"),
        ("not a new measured surface-distance",
         "a new measured surface-distance"),
        ("not-accepted", "accepted"),
        ("no new geometry or numerical limit",
         "new geometry and limits"),
    ):
        mutations.append((before, after, "boundary"))
    row_mutations = (
        (1, "must agree exactly", "may agree approximately"),
        (2, "receives no second scale conversion",
         "receives a second conversion"),
        (3, "1e-100 mm^3", "1e-100 mm"),
        (3, "130 digits for the outer jaw", "30 digits for the outer jaw"),
        (4, "separately in full-size mm and model mm", "only in full-size mm"),
        (5, "rel_tol=1e-12, abs_tol=0", "rel_tol=0, abs_tol=1e-12"),
        (6, "max(Ashape * epsilon", "min(Ashape * epsilon"),
        (6, "separate and unfused", "fused into one solid"),
        (7, "Bmodel + Bfull * f^3", "Bmodel + Bfull * f"),
        (7, "epsilon * (1 + f)", "epsilon * f"),
        (8, "must equal exact zero", "may be below epsilon"),
        (8, "(abs(a) + abs(b) + abs(c))", "(a + b + c)"),
        (9, "(Lchair + Lrail) * epsilon", "(Achair + Arail) * epsilon"),
        (9, "inner jaw 4, key 7", "inner jaw 5, key 6"),
        (10, "an edge, with zero area and no face",
         "a face with positive area"),
        (10, "2 * Nedges * epsilon", "Nedges * epsilon"),
        (11, "Positive overlap stays mandatory",
         "Positive overlap is optional"),
        (12, "a host observation only", "an independently derived oracle"),
        (13, "five individual solids", "one fused solid"),
    )
    count = 0

    def reject(candidate, expected):
        nonlocal count
        errors = _reference_criteria_errors(candidate)
        if not any(expected in error for error in errors):
            raise AssertionError(
                "reference-criteria mutation escaped or failed for the "
                "wrong reason: {}: {}".format(expected, errors)
            )
        count += 1

    for before, after, boundary in mutations:
        assert section.count(before) == 1, before
        changed = section.replace(before, after, 1)
        reject(text.replace(section, changed, 1),
               "S1 reference criteria " + boundary)
    rows = [line for line in section.splitlines() if line.startswith("|")][2:]
    for number, before, after in row_mutations:
        row = rows[number - 1]
        assert row.count(before) == 1, before
        changed = section.replace(row, row.replace(before, after, 1), 1)
        reject(text.replace(section, changed, 1),
               "S1 reference criterion {}.".format(number))
    for changed in (
        section.replace(rows[0] + "\n", "", 1),
        section.replace(rows[0], rows[1], 1),
    ):
        reject(text.replace(section, changed, 1),
               "S1 reference criteria inventory or order")
    relocated = text.replace(section, "\nNo criteria.\n", 1)
    relocated += "\n## Unrelated material\n" + section
    reject(relocated, "S1 reference criteria identity")
    return count


def main():
    text = PLAN_PATH.read_text(encoding="utf-8")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    lineage = json.loads(LINEAGE_PATH.read_text(encoding="utf-8"))
    oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
    errors = validate_plan(text, manifest, lineage, oracle)
    if errors:
        raise AssertionError("\n".join(errors))

    research_heading = "Phase 9A research and Phase 9B production boundary"
    research_section = direct_section_content(text, research_heading)
    for before, after in (
        ("and `reference-only` status", "and cleared status"),
        ("outputs stay private-development", "outputs allow commercial use"),
        ("is an output-affecting", "is not an output-affecting"),
        ("prototype facts", "prototype dimensions"),
        ("non-copyright-rights, dependency-manifest and release gates",
         "no further gates"),
        ("S1-07 through S1-13 and S1-15 keep their production-evidence "
         "obligations", "S1-07 through S1-15 are discharged"),
    ):
        assert before in research_section, before
        changed_section = research_section.replace(before, after, 1)
        _expect_invalid(
            text.replace(research_section, changed_section, 1),
            manifest, lineage, oracle, "research boundary " + before,
        )
    relocated = text.replace(research_section, "\n\nResearch is permitted.\n", 1)
    relocated += "\n## Unrelated retained material\n" + research_section
    _expect_invalid(
        relocated, manifest, lineage, oracle, "research boundary relocated",
    )

    engineering_section = direct_section_content(
        text, "Chair acceptance evidence under D-P9-005",
    )
    engineering_flat = " ".join(engineering_section.split())
    for before, after in (
        ("an independent engineering reference chain is mandatory",
         "no independent engineering reference chain is mandatory"),
        ("Before acceptance, explicit provenance and accepted numerical "
         "tolerances", "After acceptance, explicit provenance and "
         "numerical tolerances"),
        ("units, uncertainty, derivation inputs", "units only"),
        ("Do not give a Templot-derived value independent status",
         "Give a Templot-derived value independent status"),
        ("Preserve its historical Templot lineage",
         "Remove its historical Templot lineage"),
        ("is not sufficient for acceptance", "is sufficient for acceptance"),
        ("not production requirements without independent engineering",
         "production requirements without independent engineering"),
        ("Do not do more Phase 9 work", "Do more Phase 9 work"),
        ("No different Templot executable becomes", "A different Templot "
         "executable becomes"),
        ("supersedes the mandatory S1-14 comparison condition",
         "supersedes every Phase 1 evidence condition"),
        ("permission does not accept", "permission accepts"),
        ("Phase 9B stays Not started at 0/6", "Phase 9B opens at 0/6"),
    ):
        assert before in engineering_flat, before
        changed = "\n\n" + engineering_flat.replace(before, after, 1) + "\n\n"
        _expect_invalid(
            text.replace(engineering_section, changed, 1),
            manifest, lineage, oracle, "engineering boundary " + before,
        )
    relocated = text.replace(engineering_section, "\n\nNo requirements.\n", 1)
    relocated += "\n## Unrelated retained material\n" + engineering_section
    _expect_invalid(
        relocated, manifest, lineage, oracle, "engineering boundary relocated",
    )

    promoted_decision = text.replace(
        "| S1-07 | Precise prototype designation | owner-decision-required |",
        "| S1-07 | Precise prototype designation | accepted-direction |",
        1,
    )
    _expect_invalid(
        promoted_decision, manifest, lineage, oracle, "unsupported designation"
    )

    licensed_manifest = copy.deepcopy(manifest)
    licensed_manifest["subject"]["package_license"] = "CC0-1.0"
    _expect_invalid(text, licensed_manifest, lineage, oracle, "premature licence")

    cleared_lineage = copy.deepcopy(lineage)
    cleared_lineage["scopes"][0]["entries"][0][
        "current_project_status"
    ] = "project-cleared"
    _expect_invalid(text, manifest, cleared_lineage, oracle, "premature lineage")

    output_comparison = copy.deepcopy(manifest)
    output_comparison["dependencies"][1]["output_affecting"] = True
    _expect_invalid(
        text, output_comparison, lineage, oracle, "output-affecting comparison"
    )

    acceptance_section = direct_section_content(
        text, "Bounded Exit 9A-1 acceptance under D-P9-006",
    )
    for before, after in (
        ("49c72c294335898ba4e2f3cb02581c8ef6e539a7", "unreviewed-main"),
        ("df5ae7d941754ed7c18ea450d1d22559c61efbd5baaa638d2e84fa9d96b8e4c7",
         "unreviewed-package"),
        ("only for the bounded 9A-1", "for all Phase 9 exits"),
        ("remain mandatory for production", "are optional for production"),
        ("are not accepted reference", "are accepted reference"),
        ("No assisted S1 pilot", "An assisted S1 pilot"),
        ("acceptance: not-accepted", "acceptance: accepted"),
        ("Exits 9A-2 and 9A-3 stay Pending", "Exits 9A-2 and 9A-3 are accepted"),
        ("Phase 9B stays Not started at 0/6", "Phase 9B is Open at 0/6"),
    ):
        assert before in acceptance_section, before
        changed = acceptance_section.replace(before, after, 1)
        _expect_invalid(
            text.replace(acceptance_section, changed, 1),
            manifest, lineage, oracle, "Exit 9A-1 boundary " + before,
        )
    relocated = text.replace(acceptance_section, "\n\nNo acceptance.\n", 1)
    relocated += "\n## Unrelated retained material\n" + acceptance_section
    _expect_invalid(
        relocated, manifest, lineage, oracle, "Exit 9A-1 boundary relocated",
    )

    exit2_section = direct_section_content(
        text, "Bounded Exit 9A-2 acceptance under D-P9-008",
    )
    for before, after in (
        ("only for the exact frozen five-component S1 reference",
         "for every chair reference"),
        ("numerical limits stay unchanged", "numerical limits may increase"),
        ("Exit 9A-3 stays Pending", "Exit 9A-3 is accepted"),
        ("Phase 9B stays Not started", "Phase 9B is Open"),
        ("criteria-only acceptance at its date", "all-exit acceptance"),
        ("It changes no geometry", "It changes geometry"),
        ("It accepts no assisted S1 pilot", "It accepts an assisted S1 pilot"),
        ("Do not merge", "Merge"),
        ("#phase-9a-exit-2-acceptance-panel", "#unreviewed-decision"),
    ):
        assert before in exit2_section, before
        changed = exit2_section.replace(before, after, 1)
        if not _exit2_acceptance_errors(
                text.replace(exit2_section, changed, 1)):
            raise AssertionError("Exit 9A-2 mutation escaped: " + before)
    relocated = text.replace(exit2_section, "\n\nNo acceptance.\n", 1)
    relocated += "\n## Unrelated retained material\n" + exit2_section
    if not _exit2_acceptance_errors(relocated):
        raise AssertionError("Relocated Exit 9A-2 acceptance escaped")
    print("S1_EXIT2_ACCEPTANCE_MUTATIONS=10")

    exit3_section = direct_section_content(
        text, "Bounded Exit 9A-3 acceptance under D-P9-009",
    )
    for before, after in (
        ("only the frozen reference-only assisted S1 pilot", "every S1 pilot"),
        ("same neutral `ChairDefinition`", "a separate geometry system"),
        ("All 119 lineage records stay derived",
         "All records are independent"),
        ("not physical measurement calibration",
         "physical measurement calibration"),
        ("`inner-jaw`", "`replacement-jaw`"),
        ("Fastenings and plug/socket components stay outside the scope",
         "Fastenings and plug/socket components are accepted"),
        ("A null uncertainty is not zero uncertainty", "Null means zero"),
        ("unchanged 13 D-P9-007 criteria", "new numerical criteria"),
        ("leaves package metadata unchanged", "promotes package metadata"),
        ("No new numerical tolerance follows", "New tolerances follow"),
        ("Phase 9A is not closed", "Phase 9A is closed"),
        ("Phase 9B stays Not started", "Phase 9B is Open"),
        ("Do not merge or close Phase 9A", "Merge and close Phase 9A"),
        ("#phase-9a-exit-3-acceptance-panel", "#unreviewed-pilot"),
    ):
        assert before in exit3_section, before
        changed = exit3_section.replace(before, after, 1)
        if not _exit3_acceptance_errors(
                text.replace(exit3_section, changed, 1)):
            raise AssertionError("Exit 9A-3 mutation escaped: " + before)
    relocated = text.replace(exit3_section, "\n\nNo acceptance.\n", 1)
    relocated += "\n## Unrelated retained material\n" + exit3_section
    if not _exit3_acceptance_errors(relocated):
        raise AssertionError("Relocated Exit 9A-3 acceptance escaped")
    print("S1_EXIT3_ACCEPTANCE_MUTATIONS=15")

    weakened_oracle = copy.deepcopy(oracle)
    weakened_oracle["acceptance_gate"]["canonical_production_input"] = True
    _expect_invalid(text, manifest, lineage, weakened_oracle, "canonical Templot")

    count = _validate_reference_criteria_mutations(text)
    print("S1_REFERENCE_CRITERIA_MUTATIONS=" + str(count))
    print("Phase 1 S1 pilot plan validation passed")


if __name__ == "__main__":
    main()
