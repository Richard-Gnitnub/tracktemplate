#!/usr/bin/env python3
"""Bind the existing development bridge to a guarded hosted GUI session.

This module never starts FreeCAD, a display, or an unguarded workload.
The caller owns source authority, installation, deadlines and cleanup.
The readiness client makes fixed, document-free loopback requests only.
"""

import argparse
import hashlib
import http.client
import importlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import sys
import time
import xmlrpc.client

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_COMMIT = "660ed03f5dc6aeb2dd0e623cc4ed5880b4c90cb7"
PATCH_SHA256 = (
    "5914ae4390e2b2e242f65feeb35b21685b5492c11015a01f5ba5ccc26fa8bdf9"
)
CLICK_VERSION = "8.1.6"
CLICK_WHEEL = "click-8.1.6-py3-none-any.whl"
CLICK_WHEEL_BYTES = 97909
CLICK_WHEEL_SHA256 = (
    "fa244bb30b3b5ee2cae3da8f55c9e5e0c0e86093306301fb418eb9dc40fbded5"
)
CLICK_WHEEL_URL = (
    "https://files.pythonhosted.org/packages/1a/70/"
    "e63223f8116931d365993d4a6b7ef653a4d920b41d03de7c59499962821f/"
    "click-8.1.6-py3-none-any.whl"
)
PORT = 19875
SENTINEL = "TRACKTEMPLATE_COMPATIBILITY_BRIDGE_READINESS_PASS"
SOURCE_FILES = {
    "LICENSE": (26419, "20e50fe7aae3e56378ebf0417d9de904f55a0e61e4df315333e632a4d3555d95"),
    "addon/FreecadCli/__init__.py": (0, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "addon/FreecadCli/InitGui.py": (375, "43b9fe955bdd38b45d5a61a76132a238268b8af4f85fedb9022dbc91858377de"),
    "addon/FreecadCli/rpc_server.py": (6116, "c0d9dab9c41151e3948f718857b0d056e60df6c5657b01bed279b70ef5aa40c4"),
    "src/freecad_cli/__init__.py": (0, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    "src/freecad_cli/client.py": (5711, "bafd08fa7ad6e5856e3457679bd28b2b7d7072e658365b43dec973c758500f2c"),
    "src/freecad_cli/output.py": (261, "58391f1282a1a33dc87ad9f9f8e0629de0c86911e5e1dd7b1a8cd599b359f137"),
}
BASE_ENV = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
SESSION_ENV_NAMES = {
    "PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL",
    "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS", "GITHUB_ACTIONS",
    "GITHUB_SHA", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT",
    "RUNNER_ENVIRONMENT", "DISPLAY", "XAUTHORITY", "QT_QPA_PLATFORM",
    "LIBGL_ALWAYS_SOFTWARE", "GALLIUM_DRIVER", "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS", "PYTHONDONTWRITEBYTECODE",
    "PYTHONNODEBUGRANGES",
}
PROBE_CODE = """import json, os
import FreeCAD as App
from PySide6 import QtCore
application = QtCore.QCoreApplication.instance()
assert App.GuiUp
assert application is not None
assert not App.listDocuments()
assert QtCore.QThread.currentThread() == application.thread()
print(json.dumps({
    'gui_up': bool(App.GuiUp), 'documents': len(App.listDocuments()),
    'main_thread': QtCore.QThread.currentThread() == application.thread(),
    'name_present': '__name__' in globals(),
    'file_present': '__file__' in globals(), 'pid': os.getpid(),
}, sort_keys=True))
"""


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _path(value, *, directory=False, new=False):
    path = Path(value)
    _require(path.is_absolute() and ".." not in path.parts,
             "Absolute bridge path required")
    _require(not any(p.is_symlink() for p in (path, *path.parents)),
             "Bridge symbolic link refused")
    if new:
        _require(not path.exists() and path.parent.is_dir(),
                 "Fresh bridge destination required")
    else:
        _require(path.is_dir() if directory else path.is_file(),
                 "Bridge path type differs")
    return path


def _identity(content):
    return len(content), hashlib.sha256(content).hexdigest()


def _source_bytes(root):
    return {name: _path(root / name).read_bytes() for name in SOURCE_FILES}


def _check_sources(contents):
    _require(set(contents) == set(SOURCE_FILES), "Bridge closure differs")
    _require(all(_identity(contents[name]) == expected
                 for name, expected in SOURCE_FILES.items()),
             "Pinned bridge bytes differ")


def verify_checkout(checkout):
    """Verify the existing upstream and exact reviewed patch, read-only."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools import development_toolchain_preflight as preflight

    checkout = _path(checkout, directory=True)
    _path(checkout / ".git", directory=True)
    patch = _path(ROOT / "tools/freecad_bridge/freecad-cli-tracktemplate.patch")
    _require(_identity(patch.read_bytes())[1] == PATCH_SHA256,
             "Reviewed bridge patch differs")
    context = preflight.Context(root=ROOT, environ=dict(BASE_ENV))
    head = preflight._run(context, [
        "/usr/bin/git", "-C", checkout, "rev-parse", "HEAD"])
    _require(head.returncode == 0 and head.stdout.strip() == UPSTREAM_COMMIT,
             "Pinned bridge commit differs")
    _require(preflight._check_bridge_tree(
        "/usr/bin/git", checkout, patch, context) == 6,
        "Reviewed bridge tree differs")
    contents = _source_bytes(checkout)
    _check_sources(contents)
    return contents


def _wheel_bytes(path):
    path = _path(path)
    _require(path.stat().st_size == CLICK_WHEEL_BYTES,
             "Pinned Click wheel size differs")
    content = path.read_bytes()
    _require(_identity(content) == (CLICK_WHEEL_BYTES, CLICK_WHEEL_SHA256),
             "Pinned Click wheel differs")
    return content


def prepare_bridge(checkout, destination, *, click_wheel):
    """Copy only the verified runtime closure and create a private token.

    No network access, installation, runtime import or process launch occurs.
    Existing destinations are refused. The token is never in the receipt.
    """
    contents = verify_checkout(checkout)
    wheel = _wheel_bytes(click_wheel)
    destination = _path(destination, new=True)
    destination.mkdir(mode=0o700)
    for name, content in contents.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with target.open("xb") as stream:
            stream.write(content)
        target.chmod(0o644)
    with (destination / CLICK_WHEEL).open("xb") as stream:
        stream.write(wheel)
    token = destination / "rpc-token"
    with open(token, "x", opener=lambda p, flags: os.open(p, flags, 0o600)) as f:
        f.write(secrets.token_hex(32) + "\n")
    verify_bridge(destination)
    return {"schema_version": 1, "upstream_commit": UPSTREAM_COMMIT,
            "patch_sha256": PATCH_SHA256,
            "files": {name: {"bytes": size, "sha256": digest}
                      for name, (size, digest) in SOURCE_FILES.items()},
            "click_wheel": {"bytes": CLICK_WHEEL_BYTES,
                            "sha256": CLICK_WHEEL_SHA256}}


def _token(bridge_root):
    path = _path(bridge_root / "rpc-token")
    status = path.stat()
    _require(stat.S_IMODE(status.st_mode) == 0o600
             and status.st_uid == os.getuid(), "Private bridge token required")
    content = path.read_text(encoding="ascii")
    _require(re.fullmatch(r"[0-9a-f]{64}\n", content) is not None,
             "Bridge token shape differs")
    return content.strip()


def verify_bridge(bridge_root):
    """Reject changed, additional or linked staged executable material."""
    root = _path(bridge_root, directory=True)
    _require(stat.S_IMODE(root.stat().st_mode) == 0o700,
             "Private bridge directory required")
    members = set()
    for path in root.rglob("*"):
        _require(not path.is_symlink(), "Bridge symbolic link refused")
        if path.is_dir():
            continue
        _path(path)
        members.add(path.relative_to(root).as_posix())
    _require(members == set(SOURCE_FILES) | {"rpc-token", CLICK_WHEEL},
             "Staged bridge inventory differs")
    _check_sources(_source_bytes(root))
    _wheel_bytes(root / CLICK_WHEEL)
    _token(root)
    return root


def install_driver_token(bridge_root, assessment_root):
    """Supply the unchanged drivers' fixed private token path once."""
    root = verify_bridge(bridge_root)
    assessment = _path(assessment_root, directory=True)
    parent = assessment / "benchmark-output/freecad-bridge"
    _path(parent, directory=True)
    target = parent / "rpc-token"
    data = (root / "rpc-token").read_bytes()
    if target.exists() or target.is_symlink():
        _path(target)
        _require(stat.S_IMODE(target.stat().st_mode) == 0o600
                 and target.stat().st_uid == os.getuid()
                 and target.read_bytes() == data,
                 "Existing driver token differs")
    else:
        with open(target, "xb", opener=lambda p, flags: os.open(
                p, flags, 0o600)) as stream:
            stream.write(data)
    return target


def session_command(bridge_root, assessment_root, clean_env, *,
                    execution_seconds, macro=None):
    """Return explicit argv/env for the existing guarded FreeCAD GUI call."""
    root = verify_bridge(bridge_root)
    assessment = _path(assessment_root, directory=True)
    _require(type(execution_seconds) is int
             and 0 < execution_seconds <= 7200, "Bridge timeout differs")
    _require(type(clean_env) is dict
             and set(clean_env) <= SESSION_ENV_NAMES,
             "Unreviewed child environment")
    _require(all(type(v) is str and len(v) <= 4096
                 and not any(c in v for c in ("\n", "\r", "\0"))
                 for v in clean_env.values()), "Child value differs")
    _require(clean_env.get("DISPLAY") == ":99"
             and clean_env.get("QT_QPA_PLATFORM") == "xcb"
             and clean_env.get("GITHUB_ACTIONS") == "true"
             and clean_env.get("GITHUB_RUN_ATTEMPT") == "1",
             "Guarded hosted GUI environment required")
    _path(clean_env.get("XAUTHORITY", ""))
    env = dict(clean_env)
    env.update(BASE_ENV)
    env.update(FREECAD_CLI_PORT=str(PORT),
               FREECAD_CLI_TOKEN_FILE=str(root / "rpc-token"),
               FREECAD_CLI_EXECUTION_TIMEOUT=str(execution_seconds),
               TRACKTEMPLATE_REPO=str(assessment))
    argv = ["flatpak", "run", "--command=FreeCAD"]
    host_only = {"PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL",
                 "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS"}
    argv += [f"--env={name}={value}" for name, value in sorted(env.items())
             if name not in host_only]
    argv += ["org.freecad.FreeCAD", "--module-path",
             str(root / "addon/FreecadCli"), "--macro-path", str(assessment),
             "--python-path", str(assessment)]
    if macro is not None:
        argv.append(str(_path(macro)))
    return argv, env


def readiness_probe_command(bridge_root, receipt_path, *, deadline):
    """Return the client command for a child of guarded FreeCAD only.

    The caller must not launch this as an uncontained host sibling.
    Its interpreter is inside the same Flatpak as its FreeCAD parent.
    """
    root = verify_bridge(bridge_root)
    receipt = _path(receipt_path, new=True)
    _require(receipt.name == "bridge-readiness.json", "Probe name differs")
    _require(type(deadline) in (int, float) and math.isfinite(deadline)
             and deadline > 0, "Probe deadline differs")
    return (["/usr/bin/python3", "-I", "-S", "-B", str(Path(__file__)),
             "probe", "--bridge", str(root), "--receipt", str(receipt),
             "--deadline", str(deadline)], dict(BASE_ENV))


def _remaining(deadline, clock):
    remaining = deadline - clock()
    _require(math.isfinite(remaining) and remaining > 0,
             "Bridge readiness deadline exhausted")
    return min(2.0, remaining)


class _DeadlineTransport(xmlrpc.client.Transport):
    def __init__(self, deadline, clock):
        super().__init__()
        self.deadline, self.clock = deadline, clock

    def make_connection(self, host):
        _require(host == f"127.0.0.1:{PORT}", "Loopback endpoint differs")
        return http.client.HTTPConnection(
            host, timeout=_remaining(self.deadline, self.clock))


def _proxy(deadline, clock):
    return xmlrpc.client.ServerProxy(
        f"http://127.0.0.1:{PORT}",
        transport=_DeadlineTransport(deadline, clock))


def _load_client(root):
    # The verified wheel is used only by this separate contained client.
    sys.path[:0] = [str(root / "src"), str(root / CLICK_WHEEL)]
    click = importlib.import_module("click")
    _require(click.__version__ == CLICK_VERSION, "Bridge Click version differs")
    _require(str(click.__file__).startswith(str(root / CLICK_WHEEL) + "/"),
             "Bridge Click import differs")
    module = importlib.import_module("freecad_cli.client")
    _require(Path(module.__file__).resolve() == root / "src/freecad_cli/client.py",
             "Bridge client import differs")
    return module.FreeCADClient


def client_environment():
    """Return the complete credential-free environment for client children."""
    return dict(BASE_ENV)


def _process_cgroup(pid):
    lines = Path(f"/proc/{pid}/cgroup").read_text().splitlines()
    records = [line[3:] for line in lines if line.startswith("0::")]
    _require(len(records) == 1, "Unified client cgroup unavailable")
    return records[0]


def launch_readiness_probe(bridge_root, receipt_path, *, deadline,
                           guard_evidence):
    """Start the client from FreeCAD, inside its already guarded cgroup.

    Return Popen without blocking the Qt thread. The caller must poll it
    with Qt and refuse readiness on nonzero exit. Inherited raw streams
    remain in the existing guard evidence; no extra public files are made.
    This function does not create or extend a deadline or resource budget.
    """
    import FreeCAD as App

    _require(bool(App.GuiUp), "Contained GUI caller required")
    ownership = json.loads(_path(
        Path(guard_evidence) / "ownership.json").read_text())
    expected = ownership.get("cgroup")
    _require(type(expected) is str and expected.startswith("/user.slice/")
             and expected.endswith(".scope")
             and _process_cgroup("self") == expected,
             "Client parent is outside the guarded cgroup")
    command, env = readiness_probe_command(
        bridge_root, receipt_path, deadline=deadline)
    _remaining(deadline, time.monotonic)
    child = subprocess.Popen(
        command, env=env, cwd=Path(bridge_root),
        stdin=subprocess.DEVNULL, close_fds=True)
    try:
        _require(_process_cgroup(child.pid) == expected,
                 "Client escaped the guarded cgroup")
    except BaseException:
        # This exact child is ours. Its streams stay in the guard logs.
        child.kill()
        child.wait(timeout=5)
        raise
    return child


def _witness(result):
    _require(type(result) is dict and result.get("error") == "",
             "Bridge execution failed")
    data = json.loads(result.get("output", ""))
    expected = {"gui_up": True, "documents": 0, "main_thread": True,
                "name_present": False, "file_present": False}
    _require(type(data) is dict and set(data) == set(expected) | {"pid"},
             "Bridge witness fields differ")
    _require(all(type(data[k]) is type(v) and data[k] == v
                 for k, v in expected.items())
             and type(data["pid"]) is int and data["pid"] > 0,
             "Bridge witness differs")
    return data


def _probe(root, deadline, *, clock=time.monotonic, sleep=time.sleep,
           proxy_factory=_proxy, client_loader=_load_client):
    token = _token(root)
    while True:
        _remaining(deadline, clock)
        try:
            with proxy_factory(deadline, clock) as proxy:
                _require(proxy.ping(token) is True, "Bridge ping differs")
            break
        except (ConnectionRefusedError, TimeoutError):
            sleep(min(0.1, _remaining(deadline, clock)))
    with proxy_factory(deadline, clock) as proxy:
        try:
            proxy.ping("invalid-readiness-token")
        except xmlrpc.client.Fault as error:
            _require("Invalid FreeCAD CLI authentication token"
                     in error.faultString, "Authentication refusal differs")
        else:
            raise ValueError("Unauthenticated bridge accepted")
    client_type = client_loader(root)

    def call(name, *arguments):
        client = client_type(host="127.0.0.1", port=PORT,
                             timeout=_remaining(deadline, clock), token=token)
        result = getattr(client, name)(*arguments)
        _remaining(deadline, clock)
        return result

    _require(call("ping") is True, "Source client ping differs")
    synchronous = _witness(call("execute_code", PROBE_CODE))
    job = call("submit_code", PROBE_CODE)
    _require(type(job) is dict and set(job) == {"job_id", "status"}
             and job["status"] == "queued"
             and type(job["job_id"]) is str
             and re.fullmatch("[0-9a-f]{32}", job["job_id"]) is not None,
             "Bridge job identity differs")
    while True:
        result = call("get_job", job["job_id"])
        _require(type(result) is dict
                 and result.get("job_id") == job["job_id"],
                 "Bridge job response differs")
        if result.get("status") == "completed":
            asynchronous = _witness(result)
            break
        _require(result.get("status") in {"queued", "running"},
                 "Bridge async execution failed")
        sleep(min(0.1, _remaining(deadline, clock)))
    _require(synchronous == asynchronous, "Bridge process or witness changed")
    return {"schema_version": 1, "status": "PASS", "sentinel": SENTINEL,
            "upstream_commit": UPSTREAM_COMMIT, "patch_sha256": PATCH_SHA256,
            "client_imported": True, "click_version": CLICK_VERSION,
            "authenticated_ping": True, "wrong_token_refused": True,
            "synchronous": synchronous, "asynchronous": asynchronous,
            "geometry_builds": 0, "documents_opened": 0}


def probe_readiness(bridge_root, receipt_path, *, deadline):
    """Run the fixed external-client proof; publish a receipt atomically."""
    root = verify_bridge(bridge_root)
    target = _path(receipt_path, new=True)
    _require(target.name == "bridge-readiness.json", "Probe name differs")
    result = _probe(root, deadline)
    temporary = _path(target.with_suffix(".pending"), new=True)
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    # The exclusive link makes the complete receipt visible in one operation.
    os.link(temporary, target)
    temporary.unlink()
    print(SENTINEL, flush=True)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("probe",))
    parser.add_argument("--bridge", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--deadline", required=True, type=float)
    args = parser.parse_args(argv)
    _require(not sys.flags.optimize, "Bridge assertions disabled")
    probe_readiness(args.bridge, args.receipt, deadline=args.deadline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
