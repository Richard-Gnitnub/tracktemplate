"""Shared host-side helpers for the development-only FreeCAD bridge."""

import hashlib
import json
import time


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_json_output(result):
    output = str(result.get("output") or "").strip()
    if not output:
        return None
    return json.loads(output.splitlines()[-1])


def execute(client, code):
    result = client.execute_code(code)
    if result.get("error"):
        raise RuntimeError(result["error"])
    return result


def execute_file(client, path):
    return execute(client, path.read_text(encoding="utf-8"))


def submit_and_wait(client, code, label, timeout):
    submitted = client.submit_code(code)
    job_id = submitted["job_id"]
    started = time.monotonic()
    next_heartbeat = started + 30.0
    while True:
        result = client.get_job(job_id)
        status = result.get("status")
        if status == "completed":
            elapsed = time.monotonic() - started
            result["orchestrator_elapsed_seconds"] = elapsed
            print("[{}] completed in {:.2f} s".format(label, elapsed), flush=True)
            return result
        if status == "failed":
            raise RuntimeError(result.get("error") or "FreeCAD job failed")
        if status == "not_found":
            raise RuntimeError("FreeCAD forgot job {}".format(job_id))
        now = time.monotonic()
        if now >= started + timeout:
            raise TimeoutError("{} exceeded {:.0f} seconds".format(label, timeout))
        if now >= next_heartbeat:
            print("[{}] still running at {:.0f} s".format(label, now - started), flush=True)
            next_heartbeat = now + 30.0
        time.sleep(1.0)
