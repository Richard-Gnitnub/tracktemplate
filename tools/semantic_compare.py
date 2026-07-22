#!/usr/bin/env python3
"""Deterministically compare structured legacy and successor evidence."""

import hashlib
import json


SCALAR_TYPES = (type(None), bool, int, float, str)


def _type_name(value):
    return type(value).__name__


def canonical_snapshot(value):
    """Return a JSON-compatible snapshot that preserves Python container types."""
    value_type = type(value)
    if value_type in SCALAR_TYPES:
        if value_type is float:
            stored = value.hex()
        else:
            stored = value
        return {"type": _type_name(value), "value": stored}
    if value_type is dict:
        if any(type(key) is not str for key in value):
            raise TypeError("comparison mappings require string keys")
        return {
            "type": "dict",
            "items": [
                [key, canonical_snapshot(value[key])]
                for key in sorted(value)
            ],
        }
    if value_type in (list, tuple):
        return {
            "type": _type_name(value),
            "items": [canonical_snapshot(item) for item in value],
        }
    raise TypeError(
        "unsupported comparison value type: {}".format(_type_name(value))
    )


def semantic_digest(value):
    """Return the stable SHA-256 of a canonical structured snapshot."""
    payload = json.dumps(
        canonical_snapshot(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _difference(path, kind, legacy, successor):
    return {
        "path": path,
        "kind": kind,
        "legacy": canonical_snapshot(legacy),
        "successor": canonical_snapshot(successor),
    }


def _compare(path, legacy, successor, differences):
    if type(legacy) is not type(successor):
        differences.append(_difference(path, "type", legacy, successor))
        return

    if type(legacy) is dict:
        if any(type(key) is not str for key in legacy) or any(
            type(key) is not str for key in successor
        ):
            raise TypeError("comparison mappings require string keys")
        for key in sorted(set(legacy) | set(successor)):
            child_path = "{}[{}]".format(path, json.dumps(key, ensure_ascii=False))
            if key not in legacy:
                differences.append(
                    {
                        "path": child_path,
                        "kind": "unexpected-key",
                        "legacy": {"missing": True},
                        "successor": canonical_snapshot(successor[key]),
                    }
                )
            elif key not in successor:
                differences.append(
                    {
                        "path": child_path,
                        "kind": "missing-key",
                        "legacy": canonical_snapshot(legacy[key]),
                        "successor": {"missing": True},
                    }
                )
            else:
                _compare(child_path, legacy[key], successor[key], differences)
        return

    if type(legacy) in (list, tuple):
        common = min(len(legacy), len(successor))
        for index in range(common):
            _compare(
                "{}[{}]".format(path, index),
                legacy[index],
                successor[index],
                differences,
            )
        for index in range(common, len(legacy)):
            differences.append(
                {
                    "path": "{}[{}]".format(path, index),
                    "kind": "missing-item",
                    "legacy": canonical_snapshot(legacy[index]),
                    "successor": {"missing": True},
                }
            )
        for index in range(common, len(successor)):
            differences.append(
                {
                    "path": "{}[{}]".format(path, index),
                    "kind": "unexpected-item",
                    "legacy": {"missing": True},
                    "successor": canonical_snapshot(successor[index]),
                }
            )
        return

    if type(legacy) not in SCALAR_TYPES:
        canonical_snapshot(legacy)
    if type(legacy) is float:
        values_differ = legacy.hex() != successor.hex()
    else:
        values_differ = legacy != successor
    if values_differ:
        differences.append(_difference(path, "value", legacy, successor))


def compare_structures(legacy, successor):
    """Return a deterministic exact-type/value/order comparison report."""
    differences = []
    _compare("$", legacy, successor, differences)
    return {
        "schema_version": 1,
        "equal": not differences,
        "difference_count": len(differences),
        "legacy_digest": semantic_digest(legacy),
        "successor_digest": semantic_digest(successor),
        "differences": differences,
    }
