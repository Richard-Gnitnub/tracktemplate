#!/usr/bin/env python3
"""Coordinate the single approved public L1 workload on GitHub.

The workflow preserves complete diagnostics as ordinary Actions artifacts.
Approved inputs are downloaded anonymously and verified before extraction.
Approval records bind an already authorised scope; they do not authenticate
consent. Historical private-oriented filenames remain compatibility names.
"""

from contextlib import ExitStack
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import time
import traceback
from unittest.mock import patch
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import freecad_validation_guard as guard  # noqa: E402
from tools import hosted_native_geometry_pilot as original  # noqa: E402
from tools import l1_private_payload as payload  # noqa: E402


CANDIDATE = '155cbb0353ca59a144df697197d8a4a68a91beef'
ENTRY_SHA256 = '20cd1694979830099e1e6988300c1c8bc9ea1dbc59ad7a5cef1832a0fe4bcc71'
SCOPE = 'L1-current-source-600-900-600-v4'
SCOPE_SHA256 = '0bec3956e4116740d702f6f09301430999f01b2935a54ae1c48f64cf9754f20f'
INPUT_REPOSITORY = 'Richard-Gnitnub/tracktemplate'
DEPLOYMENT_ROOT = Path('/home/richard')
SENTINELS = {
    'readiness': 'L1 current-source hosted readiness passed',
    'native': 'L1 current-source hosted native validation passed',
}
SELECTORS = {
    'readiness': 'hosted_l1_current_source_suite.L1CurrentSource.test_readiness',
    'native': 'hosted_l1_current_source_suite.L1CurrentSource.test_canonical_600_900_600',
}
CONTROL_FILES = (
    '.github/workflows/l1-private-validation.yml',
    'tools/hosted_l1_private_validation.py', 'tools/l1_private_payload.py',
    'tools/freecad_validation_guard.py', 'tools/hosted_native_geometry_pilot.py',
)


TO_INPUT_HASHES = {
    "catalogue": "f1016a97f35cc87cca9e0b9f09e70ea1cec4620c43d9451430dfb299eed6b885",
    "inventory": "df8c942b3cf74508e45b8ab220c17db53912da7857109f656cda3d5f81236e93",
    "context_recipes": "e484b241fb8edc435b12a162f5eec99ba6c3a3f36100d47fb624fd07956e90a9",
    "supplemental_recipes": "fad0ddaa24eb582f9c669cc5dce9f7b68e0df66719466a3f5c1208f74132335f",
    "l1_model": "a0289c046b6ae8cb1e2df88a8f6a1f3f0dc79f7a0ae1870d0b3b13154e0eb042",
    "validation_receipt": "a91d7e9bc8f74e07a5ce8afdbe3f96c018504a40b7e6f13fa259c5c366ac24ad",
    "execution_receipt": "77967d8ee640c8aab3a2ec47d2664cf075e1d87328dff0fc1f858ab1c1ed5661",
    "build_receipt": "b3a5d11827ade1c961219efd50488aaf46fa14ca449059fd22f371e1e71b9a65",
    "s1_model": "a3c8c99a67d9f18b0ee5668400a8bf94f9f39fa641a22da7477141b74cc120eb",
    "to_base_fixture": "0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c",
}
TO_INPUT_BYTES = {
    "catalogue": 189151,
    "inventory": 6820,
    "context_recipes": 776816,
    "supplemental_recipes": 305266,
    "l1_model": 166364,
    "validation_receipt": 26770,
    "execution_receipt": 1854,
    "build_receipt": 165460,
    "s1_model": 150989,
    "to_base_fixture": 636344,
}

TO_SCOPE = "TO-001-fixed-single-rail-native-v1"
TO_ENTRY = "tests/freecad_validate_to_single_rail.py"
TO_ENTRY_SHA256 = (
    "6288286b9b7c45ec26df4cf3d2b891ae59548bab4cc5b3ab92a103fa54d627c0"
)
TO_FIXTURE_SHA256 = (
    "407040d01dd0f9c8ac275d7e4d40c928ea32a5da0a05c853bf3a1de4221a8d4b"
)
TO_CONTROL_FILES = (
    *CONTROL_FILES,
    TO_ENTRY,
    "tests/fixtures/phase9b-to-single-rail-frames.json",
    "tests/validate_to_single_rail_native_entry.py",
    "tests/validate_hosted_l1_private_validation.py",
    "tests/validate_l1_private_payload.py",
)
TO_SENTINELS = {
    "readiness": "Fixed TO single-rail hosted readiness passed",
    "native": "Fixed TO single-rail hosted native validation passed",
}
TO_SELECTORS = {
    "readiness": "freecad_validate_to_single_rail.ToSingleRail.test_readiness",
    "native": "freecad_validate_to_single_rail.ToSingleRail.test_fixed_twelve",
}
TO_COPY_NAMES = ("L1-copy.FCStd", "S1-copy.FCStd", "TO-001-copy.FCStd")


def selected_workload(environ=None):
    """Select the fixed TO workload or the unchanged default L1 proof."""
    environ = os.environ if environ is None else environ
    value = environ.get("TRACKTEMPLATE_NATIVE_WORKLOAD", "l1")
    require(value in ("l1", "to-single"), "Unsupported native workload")
    return value


def to_expected_checks(stage):
    """Return the frozen entry's independently reviewed exact counters."""
    require(stage in TO_SELECTORS, "Unsupported TO stage")
    values = dict(
        binding_checks=1,
        catalogue_contracts=2,
        source_frame_inputs=59,
        comparator_negative_controls=8,
        source_frame_comparisons=0,
        component_comparisons=0,
        successful_components=0,
        rolled_back_components=0,
        wrong_frame_rejections=0,
        preview_undo_redo=0,
    )
    if stage == "native":
        values.update(
            source_frame_comparisons=59,
            component_comparisons=270,
            successful_components=270,
            rolled_back_components=270,
            wrong_frame_rejections=2,
            preview_undo_redo=1,
        )
    return values


def validate_to_acquisition(control):
    """Require the exact source/input/publication review before transfer."""
    require(
        control.get("scope_id") == TO_SCOPE
        and control.get("entry_sha256") == TO_ENTRY_SHA256
        and isinstance(control.get("source_commit"), str)
        and re.fullmatch(r"[0-9a-f]{40}", control["source_commit"])
        and control.get("input_hashes") == TO_INPUT_HASHES
        and isinstance(control.get("handling_decision"), str)
        and control["handling_decision"].strip(),
        "TO acquisition differs",
    )
    review = control.get("publication_review", {})
    require(
        isinstance(review, dict)
        and review.get("status") == review.get("independent_review") == "PASS"
        and review.get("input_hashes") == TO_INPUT_HASHES
        and review.get("handling_decision") == control["handling_decision"]
        and isinstance(review.get("evidence_sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", review["evidence_sha256"])
        and review["evidence_sha256"] != "0" * 64
        and isinstance(review.get("publication_basis"), str)
        and review["publication_basis"].strip(),
        "Exact TO input publication review absent",
    )


def validate_to_inputs(config, manifest):
    """Bind all ten input bytes and destinations before deployment."""
    rows = config.get("inputs")
    require(
        type(rows) is list
        and len(rows) == 10
        and all(
            type(row) is dict
            and set(row)
            == {
                "id",
                "path",
                "sha256",
                "bytes",
            }
            for row in rows
        ),
        "TO input records differ",
    )
    require(
        {row["id"]: row["sha256"] for row in rows} == TO_INPUT_HASHES
        and len({row["path"] for row in rows}) == 10
        and all(
            type(row["bytes"]) is int
            and row["bytes"] == TO_INPUT_BYTES[row["id"]]
            for row in rows
        ),
        "TO input profile differs",
    )
    validate_input_map(config, manifest)
    for row in rows:
        destination = Path(row["path"])
        require(
            destination.is_absolute()
            and destination.is_relative_to(DEPLOYMENT_ROOT)
            and ".." not in destination.parts,
            "TO input destination differs",
        )


def prepare_to(stage, work):
    """Bind the current main checkout and reviewed TO control record."""
    require(os.getuid() != 0 and not sys.flags.optimize, "Unsafe interpreter")
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    admission = validate_host(os.environ, Path("/proc/meminfo").read_text())
    control = json.loads(os.environ["L1_PRIVATE_CONTROL"])
    validate_to_acquisition(control)
    require(
        control.get("stage") == stage
        and control.get("workload") == "to-single"
        and control.get("workflow_commit")
        == control["source_commit"]
        == os.environ["GITHUB_SHA"]
        == command("git", "rev-parse", "HEAD")
        and control.get("independent_review") == "PASS"
        and control.get("dispatch_nonce"),
        "Reviewed TO source differs",
    )
    access = control.get("access_review", {})
    require(
        access.get("status") == "PASS"
        and access.get("audited_at_utc")
        and access.get("owner") == "Richard-Gnitnub"
        and access.get("environment") == "l1-private-validation"
        and access.get("branches") == ["main"]
        and access.get("tags") == []
        and access.get("input_repository") == INPUT_REPOSITORY
        and access.get("repository_public") is True,
        "TO access review absent",
    )
    require(
        set(control["control_files_sha256"]) == set(TO_CONTROL_FILES),
        "TO control bindings incomplete",
    )
    for relative, expected in control["control_files_sha256"].items():
        require(
            digest(ROOT / relative) == expected, "TO control source changed"
        )
    require(
        digest(ROOT / TO_ENTRY) == TO_ENTRY_SHA256
        and digest(ROOT / "tools/freecad_validation_guard.py")
        == original.GUARD_SHA256
        and not command(
            "git", "status", "--porcelain", "--untracked-files=no"
        ),
        "Dirty or changed TO source",
    )
    write(work / "control.json", control)
    write(work / "evidence/admission.json", admission)


def acquire_to(stage, work, *, source_root=ROOT, control=None):
    """Acquire one reviewed TO profile for the native or GUI coordinator.

    The caller supplies a native acquisition record after its own scope
    checks. Runtime working documents remain outside public evidence.
    """
    require(stage in TO_SELECTORS, "Unsupported TO stage")
    if control is None:
        control = json.loads((work / "control.json").read_text())
    validate_to_acquisition(control)
    validate_host(os.environ, Path("/proc/meminfo").read_text())
    require(
        control["source_commit"]
        == os.environ.get("GITHUB_SHA")
        == command("git", "rev-parse", "HEAD", cwd=source_root)
        and digest(source_root / TO_ENTRY) == TO_ENTRY_SHA256,
        "TO acquisition source changed",
    )
    validate_input_repository()
    download_asset(control["input_archive"], work / "inputs.tar")
    manifest = payload.read_manifest(work / "inputs.tar", profile="to-single")
    extracted = payload.extract_archive(
        work / "inputs.tar", manifest, work / "unpacked", profile="to-single"
    )
    config = json.loads(extracted["run-config"].read_text())
    require(
        type(config) is dict
        and set(config)
        == {
            "schema_version",
            "scope_id",
            "source_commit",
            "entry_sha256",
            "handling_decision",
            "inputs",
        }
        and type(config["schema_version"]) is int
        and config["schema_version"] == 1
        and all(
            config[key] == control[key]
            for key in (
                "scope_id",
                "source_commit",
                "entry_sha256",
                "handling_decision",
            )
        ),
        "TO archive configuration differs",
    )
    validate_to_inputs(config, manifest)
    recovery = extracted["recovery"]
    record = json.loads(recovery.read_text())
    require(
        record.get("status") == record.get("independent_review") == "PASS"
        and record.get("checkpoint_commit") == config["source_commit"]
        and record.get("input_hashes") == TO_INPUT_HASHES,
        "TO recovery readiness absent",
    )
    # Check all targets before the first deployed byte; never rewrite paths.
    require(
        DEPLOYMENT_ROOT.is_dir()
        and DEPLOYMENT_ROOT.resolve() == DEPLOYMENT_ROOT
        and DEPLOYMENT_ROOT.stat().st_uid == os.getuid(),
        "TO deployment root unavailable",
    )
    targets = [Path(row["path"]) for row in config["inputs"]]
    for target in targets:
        require(
            not target.exists()
            and not any(p.is_symlink() for p in (target, *target.parents)),
            "Unsafe or occupied TO destination",
        )
    working = work / "test-data"
    evidence = work / "evidence/native"
    require(
        not any(p.exists() or p.is_symlink() for p in (working, evidence)),
        "TO runtime directory already exists",
    )
    for directory in (working, evidence):
        require(
            not any(p.is_symlink() for p in directory.parents),
            "Linked TO runtime directory",
        )
        directory.mkdir(mode=0o700)
    for index, row in enumerate(config["inputs"], 1):
        destination = Path(row["path"])
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with (
            extracted[row["id"]].open("rb") as source,
            destination.open("xb") as target,
        ):
            shutil.copyfileobj(source, target)
        destination.chmod(0o400)
        write(
            work / f"evidence/deployed-{index:02d}.json",
            {"path": str(destination), "sha256": row["sha256"]},
        )
    config.update(
        stage=stage,
        working_directory=str(working),
        evidence_directory=str(evidence),
        recovery={
            "path": str(recovery),
            "sha256": digest(recovery),
            "bytes": recovery.stat().st_size,
        },
    )
    write(work / "run-config.json", config)
    write(work / "evidence/run-config.json", config)
    write(work / "evidence/private-control.json", control)
    write(work / "evidence/input-manifest.json", manifest)
    shutil.copyfile(recovery, work / "evidence/recovery.json")
    if "readiness-review" in extracted:
        shutil.copyfile(
            extracted["readiness-review"],
            work / "evidence/readiness-review.json",
        )
    return config


def validate_to_receipt(stage, receipt, config):
    """Validate the whole success shape, including each exact counter."""
    expected = {
        "status": "PASS",
        "stage": stage,
        "scope_id": TO_SCOPE,
        "test_id": TO_SELECTORS[stage],
        "source_commit": config["source_commit"],
        "fixture_sha256": TO_FIXTURE_SHA256,
        "physical_fit": "NOT_PROVED",
        "input_sha256": TO_INPUT_HASHES,
        "input_bindings_unchanged": True,
        "remaining_documents": 0,
        "owned_documents_closed": True,
        "sentinel": TO_SENTINELS[stage],
    }
    fields = {*expected, "checks", "stage_timings"}
    if stage == "native":
        fields.update(
            (
                "preview_disposal_preserves_source_and_foreign",
                "component_comparisons",
            )
        )
        require(
            receipt.get("preview_disposal_preserves_source_and_foreign")
            is True,
            "TO preview disposal unproved",
        )
        validate_to_comparisons(receipt.get("component_comparisons"))
    require(
        type(receipt) is dict
        and set(receipt) == fields
        and all(
            type(receipt[key]) is type(value) and receipt[key] == value
            for key, value in expected.items()
        ),
        "TO receipt differs",
    )
    checks = receipt["checks"]
    require(
        type(checks) is dict
        and checks == to_expected_checks(stage)
        and all(type(value) is int for value in checks.values()),
        "TO exact counters differ",
    )
    times = receipt["stage_timings"]
    names = {"readiness_seconds", "cleanup_seconds", "total_seconds"}
    if stage == "native":
        names.add("native_seconds")
    require(
        type(times) is dict
        and set(times) == names
        and all(
            type(value) in (int, float)
            and 0 <= value <= limits(stage).timeout_seconds
            for value in times.values()
        ),
        "TO timing differs",
    )


def validate_to_comparisons(records):
    """Require every frozen assembly/component pair and comparator result."""
    fixture_path = ROOT / "tests/fixtures/phase9b-to-single-rail-frames.json"
    require(
        digest(fixture_path) == TO_FIXTURE_SHA256, "TO frame fixture changed"
    )
    positions = json.loads(fixture_path.read_text())["positions"]
    expected = []
    for family, bodies, fixings in (("L1", 7, 16), ("S1", 5, 12)):
        names = [f"Part_{index:02d}" for index in range(bodies)]
        names += ["SourceFixing"] + [
            f"SourceFixing{index:03d}" for index in range(1, fixings)
        ]
        expected.extend(
            (row["position_id"], name)
            for name in names
            for row in positions
            if row["family"] == family
        )
    require(
        type(records) is list and len(records) == len(expected) == 270,
        "TO component evidence incomplete",
    )
    for record, identity in zip(records, expected):
        require(
            type(record) is dict
            and set(record)
            == {
                "position_id",
                "component",
                "counts",
                "vertex_residual_mm",
            }
            and (record["position_id"], record["component"]) == identity,
            "TO component evidence identity differs",
        )
        counts, residual = record["counts"], record["vertex_residual_mm"]
        # Same EPSILON_MM as the unchanged source-bound native comparator.
        require(
            type(counts) is list
            and len(counts) == 6
            and all(type(value) is int and value >= 0 for value in counts)
            and type(residual) in (int, float)
            and 0 <= residual <= 1.0e-7,
            "TO component comparison differs",
        )


def validate_to_readiness(review, config, current_run, control):
    """Require a separately preserved, exact-source TO readiness PASS."""
    require(
        set(control["control_files_sha256"]) == set(TO_CONTROL_FILES),
        "TO readiness control bindings incomplete",
    )
    expected = {
        "status": "PASS",
        "independent_review": "PASS",
        "source_commit": config["source_commit"],
        "entry_sha256": TO_ENTRY_SHA256,
        "scope_id": TO_SCOPE,
        "workload": "to-single",
        "handling_decision": config["handling_decision"],
        "workflow_commit": control["workflow_commit"],
        "control_files_sha256": control["control_files_sha256"],
        "run_attempt": 1,
        "tests": 1,
        "skips": 0,
        "failures": 0,
        "errors": 0,
        "sentinel": TO_SENTINELS["readiness"],
        "cleanup": True,
        "evidence_verified": True,
        "independent_preservation": True,
        "input_hashes": TO_INPUT_HASHES,
        "checks": to_expected_checks("readiness"),
    }
    require(
        all(
            type(review.get(key)) is type(value) and review[key] == value
            for key, value in expected.items()
        )
        and all(type(value) is int for value in review["checks"].values()),
        "TO readiness review differs",
    )
    require(
        type(review.get("run_id")) is int
        and review["run_id"] > 0
        and str(review["run_id"]) != current_run
        and isinstance(review.get("evidence_sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", review["evidence_sha256"])
        and review["evidence_sha256"] != "0" * 64,
        "Separate TO readiness evidence absent",
    )


def to_profile_exclusion(work):
    """Keep the guard-owned private profile out of every public archive."""
    root = work / "evidence/guard/profile"
    if not root.exists() and not root.is_symlink():
        return None
    require(
        not any(p.is_symlink() for p in (root, *root.parents))
        and root.is_dir(),
        "Linked TO profile refused",
    )
    record_path = root.parent / "result.json"
    require(
        not record_path.is_symlink() and record_path.is_file(),
        "TO profile ownership receipt absent",
    )
    profile = json.loads(record_path.read_text()).get("private_profile", {})
    directories = {
        "FREECAD_USER_HOME": "user-home",
        "FREECAD_USER_DATA": "user-data",
        "FREECAD_USER_TEMP": "temp",
        "XDG_CACHE_HOME": "xdg-cache",
        "XDG_CONFIG_HOME": "xdg-config",
        "XDG_DATA_HOME": "xdg-data",
        "PYTHONPYCACHEPREFIX": "python-cache",
    }
    environment = {
        key: str(root / value) for key, value in directories.items()
    }
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    require(
        profile.get("path") == str(root)
        and profile.get("environment") == environment
        and set(p.name for p in root.iterdir())
        <= {*directories.values(), "user.cfg", "system.cfg"}
        and all((root / name).is_dir() for name in directories.values()),
        "TO guard profile differs",
    )
    inventory, total = {}, 0
    for path in (root, *sorted(root.rglob("*"))):
        require(
            not path.is_symlink()
            and path.stat().st_uid == os.getuid()
            and (path.is_dir() or path.is_file()),
            "Foreign or linked TO profile member",
        )
        name = path.relative_to(root).as_posix()
        require(
            name not in ("user.cfg", "system.cfg") or path.is_file(),
            "TO profile configuration is not a file",
        )
        inventory[name] = (
            {"sha256": digest(path), "bytes": path.stat().st_size}
            if path.is_file()
            else {"directory": True}
        )
        if path.is_file():
            total += path.stat().st_size
    return {
        "member": "guard/profile",
        "bytes": total,
        "sha256": hashlib.sha256(
            json.dumps(
                inventory,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest(),
        "reason": "private-runtime-state",
    }


def validate_to_evidence_name(name):
    """Admit only existing native diagnostic producers, never input media."""
    roots = {
        "prepare.log",
        "install.log",
        "acquisition.log",
        "execution.log",
        "finalizer.log",
        "seal.log",
        "publication.log",
        "admission.json",
        "run-config.json",
        "private-control.json",
        "input-manifest.json",
        "recovery.json",
        "readiness-review.json",
        "host.jsonl",
        "assessment.json",
        "clearance.json",
        "deadline-clearance.json",
        "emergency-cleanup.json",
        "process-finalization.json",
        "finalization.json",
        "publication.json",
    }
    roots.update(f"deployed-{index:02d}.json" for index in range(1, 11))
    groups = {
        "native": {"result.json"},
        "guard": {
            "control.json",
            "result.json",
            "ownership.json",
            "measurements.jsonl",
            "stdout",
            "stderr",
            "wrapper.stdout",
            "watchdog.json",
            "shutdown-request.json",
        },
        "finalizer-clearance": {"clearance.json", "deadline-clearance.json"},
    }
    parts = Path(name).parts
    require(
        name in roots
        or len(parts) == 2
        and parts[0] in groups
        and parts[1] in groups[parts[0]],
        "Unknown TO evidence file refused",
    )


def cleanup_to_staging(work, preserved):
    """Remove only owned TO staging after verified primary readback."""
    return cleanup_staging(work, preserved, profile="to-single")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def limits(stage):
    require(stage in SELECTORS, 'Unsupported stage')
    return guard.ValidationLimits(4096, 90 if stage == 'readiness' else 7200)


def require_finalization_time(stage, environ, now):
    """Reserve ten minutes for artifact readback within the 140-minute job."""
    started = int(environ['L1_JOB_START_SECONDS'])
    require(0 <= now - started
            <= 140 * 60 - limits(stage).timeout_seconds - 600,
            'Insufficient job time for proof and finalization')


def validate_host(environ, memory):
    require(environ.get('GITHUB_REF') == 'refs/heads/main', 'Main required')
    require(environ.get('GITHUB_RUN_ID', '').isdigit(), 'Missing run identity')
    require(not any(environ.get(name, '').lower() in ('1', 'true') for name in (
        'RUNNER_DEBUG', 'ACTIONS_STEP_DEBUG', 'ACTIONS_RUNNER_DEBUG',
    )), 'Debug logging refused')
    return original.validate_admission(environ, memory)


def child_environment(environ, config, sha256, *, workload="l1"):
    """Construct an allowlist; no tokens, secrets or caller import paths."""
    result = {key: environ[key] for key in (
        'HOME', 'PATH', 'LANG', 'LC_ALL', 'USER', 'LOGNAME',
        'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS',
        'GITHUB_ACTIONS', 'GITHUB_RUN_ID',
    ) if key in environ}
    result.update(TRACKTEMPLATE_L1_RUN_CONFIG=str(config),
                  TRACKTEMPLATE_L1_RUN_CONFIG_SHA256=sha256,
                  OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    if workload == 'to-single':
        result.pop('TRACKTEMPLATE_L1_RUN_CONFIG')
        result.pop('TRACKTEMPLATE_L1_RUN_CONFIG_SHA256')
        result.update(TRACKTEMPLATE_TO_RUN_CONFIG=str(config),
                      TRACKTEMPLATE_TO_RUN_CONFIG_SHA256=sha256)
        for key in ('GITHUB_SHA', 'GITHUB_RUN_ATTEMPT', 'RUNNER_ENVIRONMENT'):
            result[key] = environ[key]
    else:
        require(workload == 'l1', 'Unsupported native workload')
    return result


def validate_readiness(review, config, current_run, control):
    require(set(control['control_files_sha256']) == set(CONTROL_FILES),
            'Readiness control bindings incomplete')
    expected = {
        'status': 'PASS', 'independent_review': 'PASS',
        'source_commit': CANDIDATE, 'entry_sha256': ENTRY_SHA256,
        'scope_id': SCOPE, 'handling_decision': config['handling_decision'],
        'workflow_commit': control['workflow_commit'],
        'control_files_sha256': control['control_files_sha256'],
        'run_attempt': 1, 'tests': 1, 'skips': 0,
        'sentinel': True, 'cleanup': True, 'evidence_verified': True,
        'independent_preservation': True,
        'input_hashes': {row['id']: row['sha256'] for row in config['inputs']},
    }
    require(all(review.get(key) == value for key, value in expected.items()),
            'Readiness result or independent review does not match')
    require(type(review.get('run_id')) is int and review['run_id'] > 0
            and str(review['run_id']) != current_run,
            'Separate readiness run required')
    require(isinstance(review.get('evidence_sha256'), str)
            and len(review['evidence_sha256']) == 64
            and all(c in '0123456789abcdef' for c in review['evidence_sha256']),
            'Reviewed evidence identity absent')


def qualified_runtime(stdout, *, workload="l1"):
    selectors = TO_SELECTORS if workload == 'to-single' else SELECTORS
    prefix = 'TRACKTEMPLATE_B16_FOUNDATION='
    frames = [prefix, *(f'{selector.rsplit(".", 1)[1]} ({selector}) ... {prefix}'
                        for selector in selectors.values())]
    lines = [line[len(frame):] for line in stdout.splitlines()
             for frame in frames if line.startswith(frame)]
    require(stdout.count(prefix) == 1 and len(lines) == 1,
            'Expected one foundation report')
    report = json.loads(lines[0])
    require(isinstance(report, dict)
            and report.get('status') == 'modular-foundation-ready'
            and report.get('matched_profile_id') == original.EXPECTED_PROFILE
            and report.get('document_mutation') is False
            and report.get('workflow_launched') is False,
            'Qualified native foundation unproved')


def assess(stage, result, stdout, stderr, samples, clearance, *, workload="l1"):
    """Reuse the pilot's unchanged resource/count/cleanup assessment.

    Only the authorised entry's runtime record, sentinel and fixed deadline
    differ. Raw evidence and resource assertions are not rewritten.
    """
    sentinels = TO_SENTINELS if workload == 'to-single' else SENTINELS
    with ExitStack() as stack:
        for name, value in (
            ('LIMITS', limits(stage)), ('GEOMETRY_SENTINEL', sentinels[stage]),
            ('_qualified_runtime', lambda text: qualified_runtime(text, workload=workload)),
        ):
            stack.enter_context(patch.object(original, name, value))
        return original.assess_result(
            result, stdout, stderr, samples, clearance,
            deadline_clearance=clearance,
        )


def validate_native_receipt(stage, receipt):
    expected = {
        'status': 'PASS', 'stage': stage, 'profile': original.EXPECTED_PROFILE,
        'input_bindings_unchanged': True, 'owned_documents_closed': True,
        'cleanup_errors': [], 'sentinel': SENTINELS[stage],
    }
    if stage == 'native':
        expected.update(source_frame_comparisons=150, component_comparisons=138,
                        successful_preview_component_placements=690,
                        rolled_back_component_placements=230,
                        total_materialised_component_placements=920)
    else:
        expected.update(frame_input_count=150, comparator_negative_controls=8)
    require(all(receipt.get(key) == value for key, value in expected.items()),
            'Native receipt incomplete')


def paths():
    stage = os.environ['L1_STAGE']
    limits(stage)
    run = os.environ['GITHUB_RUN_ID']
    require(run.isdigit(), 'Invalid run')
    base = Path(os.environ['RUNNER_TEMP']).resolve()
    return stage, base / f'l1-private-{run}-{stage}', base / f'l1-publish-{run}-{stage}'


def command(*args, cwd=ROOT):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          check=True, timeout=15).stdout.strip()


def prepare(stage, work):
    """Validate reviewed code and public-input scope before acquisition."""
    if selected_workload() == 'to-single':
        return prepare_to(stage, work)
    require(os.getuid() != 0 and not sys.flags.optimize, 'Unsafe interpreter')
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    admission = validate_host(os.environ, Path('/proc/meminfo').read_text())
    control = json.loads(os.environ['L1_PRIVATE_CONTROL'])
    require(control['workflow_commit'] == os.environ['GITHUB_SHA']
            == command('git', 'rev-parse', 'HEAD'), 'Workflow identity changed')
    require(control['scope_id'] == SCOPE and control['scope_sha256'] == SCOPE_SHA256
            and control['stage'] == stage and control['candidate_commit'] == CANDIDATE,
            'Scope differs')
    require(control['independent_review'] == 'PASS'
            and control['handling_decision'] and control['dispatch_nonce'],
            'Reviewed handling record absent')
    access = control['access_review']
    require(access['status'] == 'PASS' and access['audited_at_utc']
            and access['owner'] == 'Richard-Gnitnub'
            and access['environment'] == 'l1-private-validation'
            and access['branches'] == ['main'] and access['tags'] == []
            and access['input_repository'] == INPUT_REPOSITORY
            and access['repository_public'] is True,
            'Owner-side access audit missing or differs')
    require(set(control['control_files_sha256']) == set(CONTROL_FILES),
            'Incomplete control source review')
    for relative, expected in control['control_files_sha256'].items():
        require(digest(ROOT / relative) == expected, 'Control source changed')
    require(digest(ROOT / 'tools/freecad_validation_guard.py') == original.GUARD_SHA256,
            'Accepted guard changed')
    candidate = ROOT / 'candidate'
    require(command('git', 'rev-parse', 'HEAD', cwd=candidate) == CANDIDATE,
            'Candidate commit differs')
    require(not command('git', 'status', '--porcelain', '--untracked-files=no',
                        cwd=candidate), 'Dirty candidate')
    require(digest(candidate / 'tests/hosted_l1_current_source_suite.py')
            == ENTRY_SHA256, 'Reviewed entry changed')
    write(work / 'control.json', control)
    write(work / 'evidence/admission.json', admission)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def download_asset(record, target, *, maximum_bytes=payload.MAX_ARCHIVE_BYTES):
    """Download only the reviewed public release asset without credentials."""
    require(type(record['asset_id']) is int and record['asset_id'] > 0,
            'Invalid asset identity')
    require(type(record['bytes']) is int and 0 < record['bytes'] <= maximum_bytes,
            'Invalid input archive size')
    url = f"https://api.github.com/repos/{INPUT_REPOSITORY}/releases/assets/{record['asset_id']}"
    request = urllib.request.Request(url, headers={
        'Accept': 'application/octet-stream',
        'X-GitHub-Api-Version': '2022-11-28',
    })
    opener = urllib.request.build_opener(NoRedirect)
    try:
        response = opener.open(request, timeout=30)
    except urllib.error.HTTPError as error:
        require(error.code == 302, 'Asset request refused')
        location = error.headers['Location']
        parsed = urllib.parse.urlsplit(location)
        require(parsed.scheme == 'https' and parsed.hostname in (
            'release-assets.githubusercontent.com', 'objects.githubusercontent.com',
        ) and not parsed.username and not parsed.password,
                'Unexpected asset redirect')
        try:
            response = opener.open(urllib.request.Request(location), timeout=30)
        except urllib.error.URLError:
            # Signed storage URLs are temporary credentials. Do not retain
            # their text in an exception, even in otherwise private logs.
            raise ValueError('Asset storage transport failed') from None
    with response, target.open('xb') as stream:
        remaining = record['bytes']
        while remaining:
            data = response.read(min(1024 * 1024, remaining))
            require(data, 'Truncated input archive')
            stream.write(data)
            remaining -= len(data)
        require(not response.read(1), 'Oversized input archive')
    require(digest(target) == record['sha256'], 'Input archive changed')


def validate_input_map(config, manifest):
    """Reject any changed destination before the first input is deployed."""
    records = {row['id']: row for row in manifest['inputs']}
    rows = config['inputs']
    require(len(rows) == len(records) == 10
            and set(records) == {row['id'] for row in rows}, 'Input set differs')
    for row in rows:
        require(all(row[field] == records[row['id']][field]
                    for field in ('path', 'sha256', 'bytes')),
                'Manifest destination or binding differs')


def emergency_cleanup(work, owner, context=None):
    """Stop only the recorded invocation and verify its remaining resources."""
    context = context or guard.GuardContext()
    records = []
    result = {'proved': False, 'commands': records}
    try:
        scope, invocation = owner['scope'], owner['invocation']
        require(re.fullmatch(r'app-flatpak-org\.freecad\.FreeCAD-[A-Za-z0-9_-]+\.scope', scope)
                and re.fullmatch(r'[0-9a-f]{32}', invocation), 'Invalid owned identity')
        relative = (f'/user.slice/user-{os.getuid()}.slice/'
                    f'user@{os.getuid()}.service/app.slice/{scope}')
        require(owner['cgroup'] == relative, 'Owned cgroup differs')
        group = context.cgroup_root / relative.lstrip('/')
        require(guard._identity(context, records, scope) == invocation,
                'Owned invocation changed')
        require(guard._kill(context, records, scope, invocation), 'Owned stop failed')
        deadline = context.monotonic() + 10
        while True:
            if not group.exists():
                result['cgroup_removed'] = True
                break
            values = {name: (group / name).read_text().strip() for name in
                      ('cgroup.events', 'cgroup.procs', 'pids.current')}
            result['cgroup_readback'] = values
            if (dict(line.split() for line in values['cgroup.events'].splitlines()).get('populated') == '0'
                    and values['cgroup.procs'] == '' and values['pids.current'] == '0'):
                break
            require(context.monotonic() < deadline, 'Owned processes remain')
            context.sleep(0.1)
        listing = guard._command(context, records, [
            'systemctl', '--user', 'list-units', '--all', '--plain', '--no-legend',
            'tracktemplate-validation-*',
        ])
        require(listing.returncode == 0, 'Deadline inventory unavailable')
        units = {line.split()[0].rsplit('.', 1)[0]
                 for line in listing.stdout.splitlines() if line.strip()}
        require(len(units) <= 32, 'Deadline inventory exceeds bounded inspection')
        matched = []
        for name in sorted(units):
            require(re.fullmatch(r'tracktemplate-validation-[0-9a-f]{32}', name),
                    'Unknown deadline unit')
            shown = guard._command(context, records, [
                'systemctl', '--user', 'show', name + '.service',
                '-p', 'ExecStart', '--value',
            ])
            match = re.search(r'argv\[\]=(.*?)\s*;', shown.stdout)
            require(shown.returncode == 0 and match, 'Deadline ownership unavailable')
            arguments = shlex.split(match.group(1))
            expected = ['/usr/bin/python3', str(ROOT / 'tools/freecad_validation_guard.py'),
                        'watchdog', scope, invocation]
            if arguments == expected:
                matched.append(name)
        require(len(matched) <= 1, 'Owned deadline is ambiguous')
        result['owned_deadlines'] = matched
        for name in matched:
            stopped = guard._command(context, records, [
                'systemctl', '--user', 'stop', name + '.timer', name + '.service',
            ])
            require(stopped.returncode == 0, 'Owned deadline stop failed')
            with patch.object(original, 'OUTPUT', work / 'evidence'):
                require(original._deadline_clearance({'cleanup_proved': True,
                                                     'watchdog': name}),
                        'Owned deadline remains')
        with patch.object(original, 'OUTPUT', work / 'evidence'):
            require(original._clearance(), 'Flatpak clearance unproved')
        result['proved'] = True
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        result['error'] = traceback.format_exc()
    return result


def acquire(stage, work):
    if selected_workload() == 'to-single':
        return acquire_to(stage, work)
    control = json.loads((work / 'control.json').read_text())
    validate_host(os.environ, Path('/proc/meminfo').read_text())
    validate_input_repository()
    download_asset(control['input_archive'], work / 'inputs.tar')
    manifest = payload.read_manifest(work / 'inputs.tar')
    extracted = payload.extract_archive(work / 'inputs.tar', manifest, work / 'unpacked')
    config = json.loads(extracted['run-config'].read_text())
    require(config['scope_id'] == SCOPE
            and config['handling_decision'] == control['handling_decision']
            and config['checkpoint_commit'] == CANDIDATE, 'Private scope differs')
    validate_input_map(config, manifest)
    recovery_record = json.loads(extracted['recovery'].read_text())
    require(recovery_record.get('status') == 'PASS'
            and recovery_record.get('independent_review') == 'PASS'
            and recovery_record.get('checkpoint_commit') == CANDIDATE
            and recovery_record.get('input_hashes') == {
                row['id']: row['sha256'] for row in config['inputs']
            }, 'Recovery readiness absent')
    deployed = []
    # This root is created/chowned by setup, never by an archive member.
    allowed = DEPLOYMENT_ROOT
    require(allowed.is_dir() and allowed.resolve() == allowed
            and allowed.stat().st_uid == os.getuid(), 'Private target root unavailable')
    for row in config['inputs']:
        destination = Path(row['path'])
        require(destination.is_absolute() and destination.is_relative_to(allowed)
                and '..' not in destination.parts and not destination.exists(),
                'Unsafe or occupied input destination')
        for parent in reversed(destination.parents):
            if parent.is_relative_to(allowed):
                require(not parent.is_symlink(), 'Linked destination refused')
                parent.mkdir(mode=0o700, exist_ok=True)
        with extracted[row['id']].open('rb') as source, destination.open('xb') as target:
            shutil.copyfileobj(source, target)
        destination.chmod(0o400)
        deployed.append(str(destination))
        write(work / f'evidence/deployed-{len(deployed):02d}.json',
              {'path': str(destination), 'sha256': row['sha256']})
    native_evidence = work / 'evidence/native'
    native_evidence.mkdir(mode=0o700)
    config.update(repository_root=str(ROOT / 'candidate'),
                  private_evidence_dir=str(native_evidence))
    recovery = extracted['recovery']
    config['recovery'] = {'path': str(recovery), 'sha256': digest(recovery),
                          'bytes': recovery.stat().st_size}
    if stage == 'native':
        require('readiness-review' in extracted, 'Readiness review absent')
        validate_readiness(json.loads(extracted['readiness-review'].read_text()),
                           config, os.environ['GITHUB_RUN_ID'], control)
    write(work / 'run-config.json', config)
    write(work / 'evidence/run-config.json', config)
    write(work / 'evidence/private-control.json', control)
    write(work / 'evidence/input-manifest.json', manifest)
    shutil.copyfile(recovery, work / 'evidence/recovery.json')
    if 'readiness-review' in extracted:
        shutil.copyfile(extracted['readiness-review'],
                        work / 'evidence/readiness-review.json')


def run(stage, work):
    workload = selected_workload()
    source_root = ROOT if workload == 'to-single' else ROOT / 'candidate'
    selectors = TO_SELECTORS if workload == 'to-single' else SELECTORS
    control = json.loads((work / 'control.json').read_text())
    validate_host(os.environ, Path('/proc/meminfo').read_text())
    require_finalization_time(stage, os.environ, time.time())
    require(command('flatpak', 'info', '--system', '--show-commit', guard.APP_ID)
            == original.APP_COMMIT, 'FreeCAD build differs')
    require(command('flatpak', 'info', '--system', '--show-runtime', guard.APP_ID)
            == original.RUNTIME, 'Runtime differs')
    require(command('flatpak', 'info', '--system', '--show-commit', original.RUNTIME)
            == original.RUNTIME_COMMIT, 'Runtime build differs')
    configuration = work / 'run-config.json'
    config = json.loads(configuration.read_text())
    if stage == 'native':
        validator = validate_to_readiness if workload == 'to-single' else validate_readiness
        validator(json.loads((work / 'unpacked/control/readiness-review.json').read_text()),
                  config, os.environ['GITHUB_RUN_ID'], control)
    samples = []

    def observe():
        try:
            row = original._memory(Path('/proc/meminfo').read_text())
            row['memory_pressure'] = Path('/proc/pressure/memory').read_text()
            row['monotonic_seconds'] = time.monotonic()
        except (OSError, ValueError) as error:
            row = {'error': repr(error)}
        samples.append(row)
        with (work / 'evidence/host.jsonl').open('a') as stream:
            stream.write(json.dumps(row) + '\n')

    def sleep(seconds):
        # Do not interfere with the guard's finally path on telemetry failure.
        try:
            observe()
        except OSError:
            samples.append({'error': 'host-evidence-write'})
        time.sleep(seconds)

    observe()
    started = time.monotonic()
    clean = child_environment(os.environ, configuration, digest(configuration),
                              workload=workload)
    argv = ['flatpak', 'run', '--command=FreeCADCmd',
            '--env=OMP_NUM_THREADS=1', '--env=OPENBLAS_NUM_THREADS=1']
    names = (('TRACKTEMPLATE_TO_RUN_CONFIG', 'TRACKTEMPLATE_TO_RUN_CONFIG_SHA256',
              'GITHUB_SHA', 'GITHUB_RUN_ATTEMPT', 'RUNNER_ENVIRONMENT')
             if workload == 'to-single' else
             ('TRACKTEMPLATE_L1_RUN_CONFIG', 'TRACKTEMPLATE_L1_RUN_CONFIG_SHA256'))
    for name in (*names, 'GITHUB_ACTIONS', 'GITHUB_RUN_ID'):
        argv.append(f'--env={name}={clean[name]}')
    argv += [guard.APP_ID, '-P', str(source_root / 'tests'), '-t', selectors[stage]]
    result = guard.run_guarded_flatpak(
        argv, limits=limits(stage), evidence_dir=work / 'evidence/guard',
        context=guard.GuardContext(sleep=sleep), cwd=source_root,
        env=clean, isolate_profile=True,
    )
    observe()
    with patch.object(original, 'OUTPUT', work / 'evidence'):
        deadline_clear = original._deadline_clearance(result)
        flatpak_clear = original._clearance()
    guard_dir = work / 'evidence/guard'
    owned = [json.loads(line) for line in (guard_dir / 'measurements.jsonl').read_text().splitlines()]
    assessment = assess(stage, result, (guard_dir / 'stdout').read_text(),
                        (guard_dir / 'stderr').read_text(), owned,
                        deadline_clear and flatpak_clear, workload=workload)
    assessment['elapsed_seconds'] = time.monotonic() - started
    assessment['initial_mem_available_bytes'] = samples[0].get('MemAvailable', 0)
    if any('error' in row for row in samples):
        assessment.update(status='FAIL', classification='EVIDENCE_INCOMPLETE')
    receipt_path = (work / 'evidence/native/result.json' if workload == 'to-single'
                    else work / f'evidence/native/{stage}/result.json')
    receipt = json.loads(receipt_path.read_text())
    try:
        if workload == 'to-single':
            validate_to_receipt(stage, receipt, config)
        else:
            validate_native_receipt(stage, receipt)
    except (KeyError, TypeError, ValueError):
        assessment.update(status='FAIL', classification='EVIDENCE_INCOMPLETE')
    assessment['native_receipt'] = receipt
    assessment['handling_decision'] = control['handling_decision']
    write(work / 'evidence/assessment.json', assessment)
    return 0 if assessment['status'] == 'PASS' else 1


def evidence_archive(work, destination, *, late=False):
    """Archive available diagnostics; omit retained input copies and bytes."""
    require(not destination.exists() and not destination.is_symlink(),
            'Evidence archive already exists')
    partial = destination.with_name(destination.name + '.partial')
    config_path = work / 'run-config.json'
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    input_hashes = {row['sha256'] for row in config.get('inputs', [])}
    records, excluded = {}, []
    to_profile = selected_workload() == 'to-single'
    if to_profile:
        exclusion = to_profile_exclusion(work)
        if exclusion is not None:
            excluded.append(exclusion)
    selected = ([work / 'evidence/publication.json', work / 'evidence/publication.log',
                 work / 'evidence/finalization.json']
                if late else sorted((work / 'evidence').rglob('*')))
    with tarfile.open(partial, 'x') as archive:
        for path in selected:
            require(not path.is_symlink(), 'Linked evidence refused')
            if to_profile and path.is_relative_to(work / 'evidence/guard/profile'):
                continue
            if path.is_file():
                name = path.relative_to(work / 'evidence').as_posix()
                if to_profile:
                    validate_to_evidence_name(name)
                identity = {'sha256': digest(path), 'bytes': path.stat().st_size}
                if name in ('native/native/L1-copy.FCStd',
                            'native/native/XO-001-copy.FCStd') or identity['sha256'] in input_hashes:
                    excluded.append({'member': name, **identity,
                                     'reason': 'restricted-input-copy'})
                    continue
                records[name] = identity
                archive.add(path, arcname='evidence/' + name, recursive=False)
        content = json.dumps({'files': records, 'excluded_inputs': excluded},
                             sort_keys=True).encode()
        info = tarfile.TarInfo('evidence-manifest.json')
        info.size, info.mode = len(content), 0o600
        archive.addfile(info, io.BytesIO(content))
    require(partial.stat().st_size <= 512 * 1024**2,
            'Evidence transport bound exceeded')
    # Expose the exact upload path only after the retained ceiling passes.
    # Hard-link creation is exclusive; a failed archive remains as .partial.
    os.link(partial, destination)
    partial.unlink()
    return {'sha256': digest(destination), 'bytes': destination.stat().st_size}


def finalize(stage, work, public):
    """Prove process cleanup; retain staged inputs until evidence readback."""
    started = time.monotonic()
    cleanup, errors = False, []
    result_path = work / 'evidence/guard/result.json'
    ownership = work / 'evidence/guard/ownership.json'
    try:
        if result_path.exists():
            result = json.loads(result_path.read_text())
            clearance_output = work / 'evidence/finalizer-clearance'
            clearance_output.mkdir(mode=0o700)
            with patch.object(original, 'OUTPUT', clearance_output):
                cleanup = original._deadline_clearance(result) and original._clearance()
            cleanup = cleanup and result.get('cleanup_proved') is True
        elif ownership.exists():
            emergency = emergency_cleanup(work, json.loads(ownership.read_text()))
            write(work / 'evidence/emergency-cleanup.json', emergency)
            cleanup = emergency['proved']
        else:
            # No owned payload exists, but setup failure still cannot PASS.
            with patch.object(original, 'OUTPUT', work / 'evidence'):
                cleanup = original._clearance()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        errors.append(traceback.format_exc())
    write(work / 'evidence/process-finalization.json', {
        'cleanup': cleanup and not errors, 'errors': errors,
        'seconds': time.monotonic() - started,
        'workflow_outcomes': {name: os.environ.get(name, '') for name in (
            'L1_PREPARE', 'L1_INSTALL', 'L1_ACQUIRE', 'L1_RUN',
        )},
    })
    # The publication step archives after this process and its outer log close.
    return 0 if not errors else 1


def cleanup_staging(work, preserved, *, profile="l1"):
    """Remove exact owned plaintext staging only after primary readback.

    This proves file absence, not secure erasure. Controls and diagnostic
    evidence remain private and are not part of this removal allowlist.
    """
    archive = work / 'evidence.tar'
    require(type(preserved.get('asset_id')) is int and preserved['asset_id'] > 0
            and preserved.get('sha256') == digest(archive)
            and preserved.get('bytes') == archive.stat().st_size,
            'Primary preservation not proved')
    process = json.loads((work / 'evidence/process-finalization.json').read_text())
    result = dict(process, staging_inputs_removed=[], staging_files_removed=[],
                  staging_absence_verified=[], primary_preservation=preserved)
    result['errors'] = list(process.get('errors', []))
    targets = [(work / 'inputs.tar', None, False)]
    targets.extend((work / 'unpacked/inputs' / name, None, False)
                   for name in payload.input_ids(profile))
    if profile == 'to-single':
        targets.extend((work / 'test-data' / name, None, False)
                       for name in TO_COPY_NAMES)
    else:
        targets.extend((work / 'evidence/native/native' / name, None, False)
                       for name in ('L1-copy.FCStd', 'XO-001-copy.FCStd'))
    try:
        require(process.get('cleanup') is True, 'Process cleanup not proved')
        if profile == 'to-single':
            directory = work / 'test-data'
            require(not any(p.is_symlink() for p in (directory, *directory.parents)),
                    'Linked TO working directory')
            if directory.exists():
                require(directory.is_dir() and directory.stat().st_uid == os.getuid()
                        and set(p.name for p in directory.iterdir()) <= set(TO_COPY_NAMES)
                        and all(p.is_file() and not p.is_symlink()
                                and p.stat().st_uid == os.getuid()
                                for p in directory.iterdir()),
                        'Unknown or linked TO working copy')
        for index in range(1, 11):
            receipt_path = work / f'evidence/deployed-{index:02d}.json'
            if not receipt_path.exists():
                continue
            require(not receipt_path.is_symlink(), 'Linked staging receipt refused')
            row = json.loads(receipt_path.read_text())
            destination = Path(row['path'])
            require(destination.is_absolute()
                    and destination.is_relative_to(DEPLOYMENT_ROOT)
                    and '..' not in destination.parts, 'Staged destination refused')
            targets.append((destination, row['sha256'], True))
    except (OSError, ValueError, KeyError, TypeError):
        result['errors'].append(traceback.format_exc())
    if not result['errors']:
        for path, expected, deployed in targets:
            try:
                require(not any(item.is_symlink() for item in (path, *path.parents)),
                        'Linked staging cleanup refused')
                if path.exists():
                    require(path.is_file() and path.stat().st_uid == os.getuid(),
                            'Staged file ownership differs')
                    identity = {'path': str(path), 'sha256': digest(path),
                                'bytes': path.stat().st_size}
                    require(expected is None or identity['sha256'] == expected,
                            'Staged input changed')
                    path.unlink()
                    result['staging_files_removed'].append(identity)
                    if deployed:
                        result['staging_inputs_removed'].append(str(path))
                require(not path.exists() and not path.is_symlink(),
                        'Staged file remains')
                result['staging_absence_verified'].append(str(path))
            except (OSError, ValueError, KeyError):
                result['errors'].append(traceback.format_exc())
    if profile == 'to-single':
        result['working_copies_absent'] = not any(
            p.exists() or p.is_symlink()
            for p in (work / 'test-data' / name for name in TO_COPY_NAMES))
        if result['errors']:
            result['working_copies_absent'] = False
    result['cleanup'] = process.get('cleanup') is True and not result['errors']
    write(work / 'evidence/finalization.json', result)
    return result


def api_request(url):
    """Read fixed GitHub metadata anonymously; refuse redirects and non-200."""
    parsed = urllib.parse.urlsplit(url)
    require(parsed.scheme == 'https' and parsed.hostname == 'api.github.com'
            and not parsed.username and not parsed.password,
            'Unsupported public endpoint')
    request = urllib.request.Request(url, headers={
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
            require(response.status == 200, 'Public metadata HTTP status differs')
            content = response.read(1024 * 1024 + 1)
            require(len(content) <= 1024 * 1024, 'Oversized GitHub metadata')
            return json.loads(content)
    except urllib.error.URLError:
        raise ValueError('Public metadata transport failed') from None


def validate_input_repository():
    metadata = api_request(f'https://api.github.com/repos/{INPUT_REPOSITORY}')
    require(metadata.get('private') is False
            and metadata.get('full_name') == INPUT_REPOSITORY
            and metadata.get('owner', {}).get('login') == 'Richard-Gnitnub',
            'Public input repository differs')


def verify_artifact(source, readback, upload, download, artifact_id):
    """Require successful same-run Actions transport and exact returned bytes."""
    require(upload == download == 'success'
            and artifact_id.isdigit() and int(artifact_id) > 0,
            'Artifact publication or download failed')
    require(not readback.is_symlink() and readback.is_file(),
            'Artifact readback unavailable')
    identity = {'sha256': digest(source), 'bytes': source.stat().st_size,
                'asset_id': int(artifact_id)}
    require(readback.stat().st_size == identity['bytes']
            and digest(readback) == identity['sha256'], 'Artifact readback differs')
    return identity


def public_summary(stage, work, evidence, publication_complete):
    assessment_path = work / 'evidence/assessment.json'
    assessment = json.loads(assessment_path.read_text()) if assessment_path.exists() else {}
    final_path = work / 'evidence/finalization.json'
    final = json.loads(final_path.read_text()) if final_path.exists() else {}
    receipt = assessment.get('native_receipt', {})
    cleanup = final.get('cleanup') is True
    passed = (assessment.get('status') == 'PASS' and cleanup
              and len(final.get('staging_inputs_removed', [])) == 10
              and publication_complete)
    if selected_workload() == 'to-single':
        passed = passed and final.get('working_copies_absent') is True
    summary = {
        'schema': 1, 'source_commit': CANDIDATE,
        'workflow_commit': os.environ['GITHUB_SHA'],
        'run_id': int(os.environ['GITHUB_RUN_ID']), 'run_attempt': 1,
        'stage': stage, 'outcome': 'PASS' if passed else 'INCOMPLETE',
        'counts': {'expected_tests': 1, 'observed_tests': assessment.get('completed_native_tests', 0),
                   'skips': assessment.get('skips', 0),
                   'expected_frames': 150 if stage == 'native' else 0,
                   'observed_frames': receipt.get('source_frame_comparisons', 0),
                   'expected_components': 138 if stage == 'native' else 0,
                   'observed_components': receipt.get('component_comparisons', 0),
                   'successful_components': receipt.get('successful_preview_component_placements', 0),
                   'rolled_back_components': receipt.get('rolled_back_component_placements', 0)},
        'flags': {'sentinel': receipt.get('sentinel') == SENTINELS[stage],
                  'input_integrity': receipt.get('input_bindings_unchanged') is True,
                  'cleanup': cleanup},
        'timings_seconds': {'total': assessment.get('elapsed_seconds', 0),
                            'readiness': receipt.get('stage_timings', {}).get('readiness_seconds', 0),
                            'native': assessment.get('elapsed_seconds', 0) if stage == 'native' else 0,
                            'finalization': final.get('seconds', 0)},
        'resources': {'memory_peak_bytes': assessment.get('peak_cgroup_memory_bytes', 0),
                      'cpu_usage_usec': assessment.get('cpu_usage_usec', 0), 'swap_peak_bytes': 0,
                      'initial_mem_available_bytes': assessment.get('initial_mem_available_bytes', 0),
                      'tasks_peak': assessment.get('peak_tasks_observed', 0)},
        'evidence': evidence,
    }
    if selected_workload() == 'to-single':
        summary.update(workload='to-single', source_commit=os.environ['GITHUB_SHA'])
        checks = receipt.get('checks', {})
        summary['counts'].update(
            expected_frames=59 if stage == 'native' else 0,
            observed_frames=checks.get('source_frame_comparisons', 0),
            expected_components=270 if stage == 'native' else 0,
            observed_components=checks.get('component_comparisons', 0),
            successful_components=checks.get('successful_components', 0),
            rolled_back_components=checks.get('rolled_back_components', 0))
        summary['flags']['sentinel'] = receipt.get('sentinel') == TO_SENTINELS[stage]
    return payload.validate_public_summary(summary, profile=selected_workload())


def seal(work):
    """Seal available diagnostics before the first standard artifact upload."""
    return evidence_archive(work, work / 'evidence.tar')


def publish(stage, work, public):
    """Verify primary readback, clean staging, and seal final diagnostics.

    The workflow performs transport with pinned ordinary artifact actions.
    A failed primary readback retains staging and is recorded in the final
    diagnostics archive. Neither transport nor cleanup is retried.
    """
    publication = {'primary': None, 'errors': [], 'retention_days': 30,
                   'delete_not_before_verified_independent_preservation': True}
    try:
        evidence = verify_artifact(
            work / 'evidence.tar', work / 'readback-primary/evidence.tar',
            os.environ.get('L1_PRIMARY_UPLOAD', ''),
            os.environ.get('L1_PRIMARY_DOWNLOAD', ''),
            os.environ.get('L1_PRIMARY_ID', ''),
        )
        publication['primary'] = evidence
        cleanup = cleanup_staging(work, evidence, profile=selected_workload())
        require(cleanup['cleanup'], 'Plaintext staging cleanup incomplete')
    except (OSError, ValueError, KeyError, TypeError):
        publication['errors'].append(traceback.format_exc())
    write(work / 'evidence/publication.json', publication)
    # Include all available diagnostics when the first upload failed too.
    evidence_archive(work, work / 'publication.tar')
    return 0 if not publication['errors'] else 1


def complete(stage, work, public):
    """Verify final artifact readback before emitting the fixed summary."""
    evidence = {'sha256': '0' * 64, 'bytes': 0, 'asset_id': 0}
    complete = False
    try:
        evidence = verify_artifact(
            work / 'publication.tar', work / 'readback-final/publication.tar',
            os.environ.get('L1_FINAL_UPLOAD', ''),
            os.environ.get('L1_FINAL_DOWNLOAD', ''),
            os.environ.get('L1_FINAL_ID', ''),
        )
        publication = json.loads((work / 'evidence/publication.json').read_text())
        complete = (os.environ.get('L1_PUBLICATION') == 'success'
                    and publication['primary'] is not None
                    and not publication['errors'])
    except (OSError, ValueError, KeyError, TypeError):
        complete = False
    # The final artifact already contains all diagnostic generation. These
    # fixed-schema operations cannot convert missing evidence into PASS.
    try:
        public.mkdir(mode=0o700, exist_ok=True)
        write(public / 'summary.json', public_summary(stage, work, evidence, complete))
        return 0 if complete else 1
    except (OSError, ValueError, KeyError, TypeError):
        return 1

def main():
    require(len(sys.argv) == 2, 'Expected one fixed operation')
    stage, work, public = paths()
    operation = sys.argv[1]
    if operation == 'prepare':
        prepare(stage, work)
    elif operation == 'acquire':
        acquire(stage, work)
    elif operation == 'run':
        return run(stage, work)
    elif operation == 'finalize':
        return finalize(stage, work, public)
    elif operation == 'seal':
        seal(work)
    elif operation == 'complete':
        return complete(stage, work, public)
    elif operation == 'publish':
        return publish(stage, work, public)
    elif operation == 'finish':
        try:
            summary = json.loads((public / 'summary.json').read_text())
            payload.validate_public_summary(summary, profile=selected_workload())
            return 0 if summary['outcome'] == 'PASS' and os.environ.get('L1_SUMMARY_UPLOAD') == 'success' else 1
        except (OSError, ValueError, KeyError):
            return 1
    else:
        raise ValueError('Unsupported operation')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (Exception, KeyboardInterrupt):
        # The outer shell must already point both descriptors at evidence logs.
        traceback.print_exc()
        raise SystemExit(1) from None
