"""Build the finite reviewed diagnostic successor before matrix execution.

Only named expressions in exact assessment predecessors change. The
original message expressions still evaluate once on their original failure
branches. Original report arguments evaluate in their original order, and
full rendered text is retained privately before a public hash witness.
No running exception or captured stdout/stderr is intercepted here.
"""

import ast
import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import stat

from tools import prepare_runtime_assessment as assessment


SESSION_ENV = "TRACKTEMPLATE_DIAGNOSTIC_SESSION"
REPORT_DIRECTORY = "diagnostic-private"
REPORT_MARKER = "TRACKTEMPLATE_PRIVATE_REPORT="
MESSAGE_MARKER = "TT_DIAGNOSTIC"

# Each tuple names one exact AST expression, never a broad node class.
SOURCES = {'tests/freecad_gui_validate_phase5_transition_coin_viewprovider.py': {'original_sha256': 'd03856ec4277ce245d09d0ab457461503c07176f94aba93d312de712317d4900',
                                                                       'predecessor_sha256': 'd03856ec4277ce245d09d0ab457461503c07176f94aba93d312de712317d4900',
                                                                       'sites': (('message',
                                                                                  387,
                                                                                  'g05-selection',
                                                                                  '',
                                                                                  '37cf9ed3e7bbeb608f4ac9127bcd0d1700dff0fe4f1e95d155c12db0224b7582'),)},
 'tests/freecad_gui_validate_phase5_transition_multi_object_edit.py': {'original_sha256': '86257a847d4b1b4553f92785df96acedc28d294d4fa76d5e159594db800660af',
                                                                       'predecessor_sha256': '86257a847d4b1b4553f92785df96acedc28d294d4fa76d5e159594db800660af',
                                                                       'sites': (('message',
                                                                                  1041,
                                                                                  'g05-multi-selection',
                                                                                  '',
                                                                                  '0c3ebb33dffdb6e73becd8fd13e4e3dae5ea4586acc94dbee9905d4f7f9ff562'),)},
 'tests/freecad_validate_phase7_connected_straight_validation.py': {'original_sha256': '00aa8f2127b20a63679ffb667fccedb249feaa0072873ff3d4e42489be82b66f',
                                                                    'predecessor_sha256': '7573579c7499af53b7116f65b333086a867a5187a44aa1e959d4bd939ce02769',
                                                                    'sites': (('report',
                                                                               216,
                                                                               'n24-report',
                                                                               '',
                                                                               'e8bcbc8c85015ab6b33eeacee88ba6a4dcd282d01dd7d43e8ae7ae554c55db78'),)},
 'tests/freecad_validate_phase7_platform_input_validation.py': {'original_sha256': '68c5e7e013430775a117cf5ebdb252204403adc4a289490529494e906e125e5e',
                                                                'predecessor_sha256': '8299d77114071418d052b415544fa33216a2996dc4de82cc1fc940a75052d2c4',
                                                                'sites': (('report',
                                                                           240,
                                                                           'n29-report',
                                                                           '',
                                                                           'e8bcbc8c85015ab6b33eeacee88ba6a4dcd282d01dd7d43e8ae7ae554c55db78'),)},
 'tests/freecad_validate_phase7_platform_longitudinal_bounds.py': {'original_sha256': 'cf0860828bfbd65300d6c22cf6cad7158e91044314cb2fb4b8f610f9b4520fb3',
                                                                   'predecessor_sha256': '74af4d6c91327c92bed5928bef4dcb119ac1fdd23f5822366f8798e361ae852b',
                                                                   'sites': (('report',
                                                                              294,
                                                                              'n30-report',
                                                                              '',
                                                                              'e8bcbc8c85015ab6b33eeacee88ba6a4dcd282d01dd7d43e8ae7ae554c55db78'),)},
 'tests/freecad_validate_phase7_platform_top_heights.py': {'original_sha256': '39ea194df400cd7ed0dc30a1cc6f2764a68dc300bc1617274a44440569931b22',
                                                           'predecessor_sha256': '486a90a8ce3d6afea1e7942d6b1b58166f1fbfda84d29dc3e33648993dc3eb44',
                                                           'sites': (('report',
                                                                      281,
                                                                      'n31-report',
                                                                      '',
                                                                      'e8bcbc8c85015ab6b33eeacee88ba6a4dcd282d01dd7d43e8ae7ae554c55db78'),)},
 'tests/freecad_validate_phase8_crossover_b4_recovery.py': {'original_sha256': '670404a948f9bfae8098b63bc19999e4e9766447237ffe7cb259d396b544e9d6',
                                                            'predecessor_sha256': 'dfc7e44fc4d3ab6dbba7aa234d5e88ec1bb7877dab5d0a0fbe598959f8c6f3fa',
                                                            'sites': (('message',
                                                                       153,
                                                                       'n36-returned',
                                                                       '',
                                                                       '8b3d01a0027ea9b78a3b550d53cdb244080cfe52998b0a18948c9331454c9f41'),
                                                                      ('message',
                                                                       156,
                                                                       'n36-analysis',
                                                                       '',
                                                                       '6bb0c3203ec9f6122a12893a52541d01c41d1441b5febc853d83e09ab60ee74b'))},
 'tests/freecad_validate_phase8_crossover_host_integration_recovery.py': {'original_sha256': '42cc5d577a5e0891ab0f26870683921d31a60f2e518fe3a05dec580db4c1e441',
                                                                          'predecessor_sha256': '8ffba31f4616fc4a880b1254588dd5b81126a4e42c2eeea50150315733cc6cda',
                                                                          'sites': (('message',
                                                                                     174,
                                                                                     'n38-reopen',
                                                                                     '',
                                                                                     'aaf8ad9ee72ee8e116727cf1143d847d7dbef7180cb1bf829937fcb02abb678b'),
                                                                                    ('raise',
                                                                                     217,
                                                                                     'n38-state',
                                                                                     '',
                                                                                     '8035489aa916359d38ae24222741631cfb71b1536cf4318afe75885870dacb5b'))},
 'tests/freecad_validate_phase8_turnout_selected_export.py': {'original_sha256': '3d00a5588090f9ddad9bccee8daed5fea736fa35c1b283741eaa0dd3480c5bc8',
                                                              'predecessor_sha256': '1d4495583510098d238e7afcf34435519ab8dda82dc7726e682bc303d78a2c6a',
                                                              'sites': (('message',
                                                                         326,
                                                                         'n47-row',
                                                                         '',
                                                                         'f892344c43095a48ac86c0a54a4f2c837553519a1b1af71ebf121f69d7e448b2'),)},
 'tests/freecad_validate_phase9a_chair_base.py': {'original_sha256': '02f3acd98d908a56edf32e093eea899d4c13a35cd6821252a9c077d749b3bce2',
                                                  'predecessor_sha256': '02f3acd98d908a56edf32e093eea899d4c13a35cd6821252a9c077d749b3bce2',
                                                  'sites': (('report',
                                                             210,
                                                             'n49-report',
                                                             '',
                                                             '0e0291155c907ef8074f96de13173716307c6cef79f901a0bdea2f56138dbf62'),)},
 'tests/freecad_validate_phase9a_chair_key.py': {'original_sha256': '3000b120f4dc499619ac9865706177943d241b5818a7df4468d60efcc61a9de4',
                                                 'predecessor_sha256': '3000b120f4dc499619ac9865706177943d241b5818a7df4468d60efcc61a9de4',
                                                 'sites': (('report',
                                                            191,
                                                            'n50-report',
                                                            '',
                                                            '8cd2b3d6bd52a8807ac2a1ddab3391308ed2bfb82c2f1afda58c091b38d31fc1'),)},
 'tests/freecad_validate_phase9a_chair_outer_jaw.py': {'original_sha256': '4107cd11fff3a3aa394f30bd99033d7f9efc73e460cfa45366c0df29c736fe90',
                                                       'predecessor_sha256': '4107cd11fff3a3aa394f30bd99033d7f9efc73e460cfa45366c0df29c736fe90',
                                                       'sites': (('report',
                                                                  262,
                                                                  'n51-report',
                                                                  '',
                                                                  '2355e1edb9809f1534f8845d454dcc0cde6c686f1550b2790e0366ac55bcb6c2'),)},
 'tests/freecad_validate_phase9a_chair_seat.py': {'original_sha256': 'd922406e093e89a5940472f1ffee03ec08b1911a7c9a58f1c2141a6c26f5e643',
                                                  'predecessor_sha256': 'd922406e093e89a5940472f1ffee03ec08b1911a7c9a58f1c2141a6c26f5e643',
                                                  'sites': (('report',
                                                             141,
                                                             'n52-report',
                                                             '',
                                                             'd5358c17fb5bd3f7806e93cff7997b399162929e55b598cf41d5155051724f80'),)},
 'tools/freecad_bridge/probes/b14_ordinary_edit_driver.py': {'original_sha256': '62ae62702155200e01576463145bb0de018bfcf7a0aae0c42b0782aabfde2c58',
                                                             'predecessor_sha256': '62ae62702155200e01576463145bb0de018bfcf7a0aae0c42b0782aabfde2c58',
                                                             'sites': (('raise',
                                                                        446,
                                                                        'g03-inputs',
                                                                        '',
                                                                        '5cdcf6a6de6d8a9c91f7482a1b523f3cf576bf8db1e087620c308a7901187dbc'),)},
 'tools/freecad_bridge/probes/b14_straight_station_driver.py': {'original_sha256': '20b2c4b038637b43b6eb57fdc95b8f3df0d8e0203afc7793492d1a966fdec72f',
                                                                'predecessor_sha256': '20b2c4b038637b43b6eb57fdc95b8f3df0d8e0203afc7793492d1a966fdec72f',
                                                                'sites': (('raise',
                                                                           141,
                                                                           'g00-routes',
                                                                           '',
                                                                           'b56d7c6717afcf81e62fccca03e78aaa63916006ed3f65078958a74b086157be'),)},
 'tools/freecad_bridge/run_phase5_transition_viewprovider.py': {'original_sha256': '17cc6a0e2db06d849ca5e19de13ac8d48cfc6d21502c572cc17fbc47a4429cbd',
                                                                'predecessor_sha256': 'b1c258de42f4a403491dbd1b19879dca35d9441aa06d206ae63fe798e555abba',
                                                                'sites': (('report',
                                                                           488,
                                                                           'g05-report',
                                                                           'TRACKTEMPLATE_PHASE5_VIEWPROVIDER_GUI=',
                                                                           'e880169f1f1b148bd5c1c2177be30a190d81d97c9c845562250dbad715200a1e'),)},
 'tools/freecad_bridge/run_phase8_crossover_edit_recovery_gui.py': {'original_sha256': '06ca874aac2b34ba002f4671edc5f86aa78354e30b0644372554e952adee97b3',
                                                                    'predecessor_sha256': 'ae8e19fdb1f8d03530ba5a087376c0fec794797ac7d1f153f02a52d9c5a3ed78',
                                                                    'sites': (('embedded-raise',
                                                                               335,
                                                                               'g08-edit-preview',
                                                                               '',
                                                                               '04b4bd54756c1e51774b95a3f8f1e067a62f656472f02d8b7327d7dbf7c8504d'),)},
 'tools/freecad_bridge/run_phase8_crossover_preflight_gui.py': {'original_sha256': 'b0d35344d3d454a5617f5b500e9ab0fe0663761455760e2c78b23d72cd841e09',
                                                                'predecessor_sha256': '39a2f1c200bafd98d448d2934e8fd056c2d0589c33dabe283e4f8aa643ac2469',
                                                                'sites': (('embedded-raise',
                                                                           174,
                                                                           'g08-preview',
                                                                           '',
                                                                           '2d093417d5c2c3c51c5ea0ede21fbe1ff4f417a7b0ac360a81e315c17aeb9e39'),)},
 'tools/freecad_bridge/run_phase8_straight_host_crossover_gui.py': {'original_sha256': '51d9a5b324e24b8998140f8a8c6d10014e767fe298778b828a29af2041e52a87',
                                                                    'predecessor_sha256': '038611e976bf19580a5bf43f593e5c2577bee5e81d81258bbcedc3c42e53ca26',
                                                                    'sites': (('embedded-raise',
                                                                               603,
                                                                               'g08-straight-preview',
                                                                               '',
                                                                               'b93f5c855993bec3d59854968885bac360302cb0c56239742eff21f4429d1fd8'),
                                                                              ('embedded-raise',
                                                                               815,
                                                                               'g08-straight-edit',
                                                                               '',
                                                                               '3d4b01f042c9df283c76843d0a568a6546173b26eb41f5fa136b24e06ffdd7a9'))},
 'tools/freecad_bridge/straight_station_recipe.py': {'original_sha256': 'df6ba6590fcc800240c2486e502bb2f0559196540aa54ea532fcff97dc33e183',
                                                     'predecessor_sha256': 'df6ba6590fcc800240c2486e502bb2f0559196540aa54ea532fcff97dc33e183',
                                                     'sites': (('raise',
                                                                289,
                                                                'g00-route',
                                                                '',
                                                                '9e1dd74558428b23be4efee58954e40da93c7f662d2ff516b19846e95b55e8f4'),)},
 'tracktemplate/compatibility/b15_workflow_host.py': {'original_sha256': 'd4667ae56b27a11605da9b6b69f59a1de68e72b074bf78bd00a2ccb8f74205d4',
                                                      'predecessor_sha256': 'd4667ae56b27a11605da9b6b69f59a1de68e72b074bf78bd00a2ccb8f74205d4',
                                                      'sites': (('loader',
                                                                 193,
                                                                 'b15-compile',
                                                                 '',
                                                                 '6238f97a67df1469a706c165e0d39eb7880a9515706b8fdb5a1bf6cfedcbdad0'),)}}


# This exact source is inserted into each affected disposable assessment
# module. Imports stay inside the helpers; no product import is redirected.
INLINE_HELPERS = r'''
def _tt_diagnostic_message(site, value):
    import hashlib as _tt_hashlib
    if _TT_DIAGNOSTIC_SITES.get(site, (None,))[0] not in ("message", "raise", "embedded-raise"):
        raise ValueError("Diagnostic message site differs")
    rendered = str(value).encode("utf-8")
    return "TT_DIAGNOSTIC site=" + site + " value_sha256=" + (
        _tt_hashlib.sha256(rendered).hexdigest()
    )


def _tt_diagnostic_private(site, raw, instance=0):
    import hashlib as _tt_hashlib
    import json as _tt_json
    import os as _tt_os
    from pathlib import Path as _tt_Path
    import stat as _tt_stat
    binding = _TT_DIAGNOSTIC_SITES.get(site)
    if binding is None or binding[0] not in ("report", "console"):
        raise ValueError("Diagnostic private report site differs")
    filename = site + ("-%04d" % instance if instance else "") + ".txt"
    witness = {
        "site": site, "bytes": len(raw),
        "sha256": _tt_hashlib.sha256(raw).hexdigest(),
    }
    if instance:
        witness["instance"] = instance
    encoded_witness = (_tt_json.dumps(witness, sort_keys=True) + "\n").encode()
    session = _tt_Path(_tt_os.environ.get(
        "TRACKTEMPLATE_DIAGNOSTIC_SESSION", ""
    ))
    if not session.is_absolute() or ".." in session.parts:
        raise ValueError("Diagnostic session is not absolute")
    if any(part.is_symlink() for part in (session, *session.parents)):
        raise ValueError("Diagnostic session contains a symbolic link")
    session_fd = _tt_os.open(
        session, _tt_os.O_RDONLY | _tt_os.O_DIRECTORY | _tt_os.O_NOFOLLOW
    )
    try:
        metadata = _tt_os.fstat(session_fd)
        if (metadata.st_uid != _tt_os.getuid()
                or _tt_stat.S_IMODE(metadata.st_mode) != 0o700):
            raise ValueError("Diagnostic session is not private and owned")
        try:
            _tt_os.mkdir("diagnostic-private", 0o700, dir_fd=session_fd)
        except FileExistsError:
            pass
        private_fd = _tt_os.open(
            "diagnostic-private", _tt_os.O_RDONLY | _tt_os.O_DIRECTORY
            | _tt_os.O_NOFOLLOW, dir_fd=session_fd,
        )
        try:
            metadata = _tt_os.fstat(private_fd)
            if (metadata.st_uid != _tt_os.getuid()
                    or _tt_stat.S_IMODE(metadata.st_mode) != 0o700):
                raise ValueError("Diagnostic report directory differs")
            descriptor = _tt_os.open(
                filename, _tt_os.O_WRONLY | _tt_os.O_CREAT
                | _tt_os.O_EXCL | _tt_os.O_NOFOLLOW, 0o600,
                dir_fd=private_fd,
            )
            with _tt_os.fdopen(descriptor, "wb") as destination:
                destination.write(raw)
                destination.flush()
                _tt_os.fsync(destination.fileno())
        finally:
            _tt_os.close(private_fd)
        witness_fd = _tt_os.open(
            "diagnostic-witnesses.jsonl", _tt_os.O_WRONLY | _tt_os.O_CREAT
            | _tt_os.O_APPEND | _tt_os.O_NOFOLLOW, 0o600, dir_fd=session_fd,
        )
        with _tt_os.fdopen(witness_fd, "ab") as witness_stream:
            metadata = _tt_os.fstat(witness_stream.fileno())
            if (not _tt_stat.S_ISREG(metadata.st_mode)
                    or metadata.st_nlink != 1
                    or metadata.st_uid != _tt_os.getuid()
                    or _tt_stat.S_IMODE(metadata.st_mode) != 0o600
                    or metadata.st_size > 16384):
                raise ValueError("Diagnostic witness sidecar differs")
            witness_stream.write(encoded_witness)
            witness_stream.flush()
            _tt_os.fsync(witness_stream.fileno())
    finally:
        _tt_os.close(session_fd)
    prefix = binding[1] or "TRACKTEMPLATE_PRIVATE_REPORT="
    return prefix + _tt_json.dumps(witness, sort_keys=True)


def _tt_diagnostic_report(site, *values, **keywords):
    import builtins as _tt_builtins
    import io as _tt_io
    if _TT_DIAGNOSTIC_SITES.get(site, (None,))[0] != "report":
        raise ValueError("Diagnostic report site differs")
    if set(keywords) - {"sep", "end", "flush"}:
        raise ValueError("Diagnostic report keywords differ")
    stream = _tt_io.StringIO()
    _tt_builtins.print(*values, file=stream, **keywords)
    raw = stream.getvalue().encode("utf-8")
    _tt_builtins.print(_tt_diagnostic_private(site, raw),
                       flush=keywords.get("flush", False))


def _tt_diagnostic_console(site, value):
    import os as _tt_os
    if _TT_DIAGNOSTIC_SITES.get(site, (None,))[0] != "console":
        raise ValueError("Diagnostic console site differs")
    key = (_tt_os.environ.get("TRACKTEMPLATE_DIAGNOSTIC_SESSION"), site)
    instance = _TT_DIAGNOSTIC_COUNTS.get(key, 0) + 1
    if instance > 9:
        raise ValueError("Diagnostic console occurrence bound exceeded")
    _TT_DIAGNOSTIC_COUNTS[key] = instance
    return _tt_diagnostic_private(site, value.encode("utf-8"), instance) + "\n"


def _tt_diagnostic_b15_tree(tree, source):
    import ast as _tt_ast
    import copy as _tt_copy
    import hashlib as _tt_hashlib
    if _tt_hashlib.sha256(source.encode("utf-8")).hexdigest() != (
        "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848"
    ):
        raise ValueError("Diagnostic B15 original fingerprint differs")
    original = _tt_ast.parse(source)
    original.body.pop()
    if _tt_ast.dump(tree, include_attributes=False) != _tt_ast.dump(
            original, include_attributes=False):
        raise ValueError("Diagnostic B15 loader AST differs")
    changed = _tt_copy.deepcopy(tree)
    candidates = [node for node in _tt_ast.walk(changed)
                  if isinstance(node, _tt_ast.Call)
                  and getattr(node, "lineno", 0) == 38693
                  and isinstance(node.func, _tt_ast.Attribute)
                  and node.func.attr == "PrintWarning"]
    if len(candidates) != 1:
        raise ValueError("Diagnostic B15 console site differs")
    call = candidates[0]
    if (len(call.args) != 1 or call.keywords
            or _tt_ast.unparse(call.func) != "App.Console.PrintWarning"
            or _tt_hashlib.sha256(_tt_ast.dump(
                call.args[0], include_attributes=False).encode()).hexdigest()
            != "c996ae42a2eaec470c4740ff7ff03b0873fe84f36fd3b7ba917b9718e419d096"):
        raise ValueError("Diagnostic B15 console argument differs")
    original_argument = call.args[0]
    call.args[0] = _tt_ast.copy_location(_tt_ast.Call(
        func=_tt_ast.Name(id="_tt_diagnostic_console", ctx=_tt_ast.Load()),
        args=[_tt_ast.Constant(value="b15-console"), original_argument],
        keywords=[]), original_argument)
    _tt_ast.fix_missing_locations(changed)
    return changed

'''


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _identity(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _ast_hash(node):
    return _identity(ast.dump(node, include_attributes=False).encode())["sha256"]


def _selected_node(tree, kind, line):
    selected = []
    for node in ast.walk(tree):
        if getattr(node, "lineno", 0) != line:
            continue
        if kind == "message" and isinstance(node, ast.Assert):
            selected.append(node.msg)
        elif kind == "raise" and isinstance(node, ast.Raise):
            _require(isinstance(node.exc, ast.Call)
                     and isinstance(node.exc.func, ast.Name)
                     and node.exc.func.id in (
                         "AssertionError", "ValueError", "RuntimeError")
                     and len(node.exc.args) == 1 and not node.exc.keywords,
                     "Diagnostic exception constructor differs")
            selected.append(node.exc.args[0])
        elif (kind == "report" and isinstance(node, ast.Call)
              and isinstance(node.func, ast.Name) and node.func.id == "print"):
            selected.append(node)
    _require(len(selected) == 1 and selected[0] is not None,
             "Diagnostic source site is missing or ambiguous")
    return selected[0]


def _span(raw, node):
    lines = raw.splitlines(keepends=True)
    return (sum(map(len, lines[:node.lineno - 1])) + node.col_offset,
            sum(map(len, lines[:node.end_lineno - 1])) + node.end_col_offset)


def _helper_source(binding):
    sites = {site: (kind, prefix)
             for kind, _, site, prefix, _ in binding["sites"]}
    kinds = {value[0] for value in sites.values()}
    names = set()
    if kinds & {"message", "raise", "embedded-raise"}:
        names.add("_tt_diagnostic_message")
    if "report" in kinds:
        names.update(("_tt_diagnostic_report", "_tt_diagnostic_private"))
    if "loader" in kinds:
        sites["b15-console"] = ("console", "")
        names.update(("_tt_diagnostic_console", "_tt_diagnostic_private",
                      "_tt_diagnostic_b15_tree"))
    helpers = "\n\n".join(ast.get_source_segment(INLINE_HELPERS, node)
                            for node in ast.parse(INLINE_HELPERS).body
                            if isinstance(node, ast.FunctionDef)
                            and node.name in names)
    counts = "_TT_DIAGNOSTIC_COUNTS = {}\n" if "loader" in kinds else ""
    return ("\n\n_TT_DIAGNOSTIC_SITES = " + repr(sites) + "\n"
            + counts + helpers + "\n\n")


def _embedded_sites(tree, sites):
    result = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant)
                and isinstance(node.value, str) and "\n" in node.value):
            continue
        try:
            inner = ast.parse(node.value)
        except SyntaxError:
            continue
        matching = []
        for kind, line, site, prefix, digest in sites:
            if kind != "embedded-raise":
                continue
            inner_line = line - node.lineno + 1
            raises = [item for item in ast.walk(inner)
                      if isinstance(item, ast.Raise)
                      and item.lineno == inner_line]
            if raises:
                expression = _selected_node(inner, "raise", inner_line)
                _require(_ast_hash(expression) == digest,
                         "Embedded diagnostic expression changed")
                matching.append((kind, inner_line, site, prefix, digest))
        if matching:
            result.append((node, inner, matching))
    _require(sum(len(row[2]) for row in result)
             == sum(site[0] == "embedded-raise" for site in sites),
             "Embedded diagnostic site missing or ambiguous")
    return result


def _wrap_expression(raw, tree, sites):
    replacements = []
    for kind, line, site, _prefix, digest in sites:
        if kind == "loader":
            calls = [node for node in ast.walk(tree)
                     if isinstance(node, ast.Call) and node.lineno == line
                     and isinstance(node.func, ast.Name)
                     and node.func.id == "compile"]
            _require(len(calls) == 1, "Diagnostic loader compile site differs")
            node = calls[0].args[0]
        else:
            node = _selected_node(tree, "raise" if kind == "embedded-raise"
                                  else kind, line)
        _require(_ast_hash(node) == digest, "Diagnostic expression changed")
        start, end = _span(raw, node)
        expression = raw[start:end]
        if kind == "report":
            _require(expression.startswith(b"print("),
                     "Diagnostic print spelling differs")
            replacement = (b"_tt_diagnostic_report(" + repr(site).encode()
                           + b", " + expression[len(b"print("):])
        elif kind == "loader":
            replacement = b"_tt_diagnostic_b15_tree(" + expression + b", source)"
        else:
            replacement = (b"_tt_diagnostic_message(" + repr(site).encode()
                           + b", (" + expression + b"))")
        replacements.append((start, end, replacement))
    for start, end, replacement in sorted(replacements, reverse=True):
        raw = raw[:start] + replacement + raw[end:]
    return raw


def _insert_helpers(raw, binding):
    tree = ast.parse(raw)
    insertion_line = 0
    for index, node in enumerate(tree.body):
        if (index == 0 and isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            insertion_line = node.end_lineno
        elif isinstance(node, ast.ImportFrom) and node.module == "__future__":
            insertion_line = node.end_lineno
        else:
            break
    offset = sum(map(len, raw.splitlines(keepends=True)[:insertion_line]))
    return raw[:offset] + _helper_source(binding).encode() + raw[offset:]


LOADER_BINDING = (
    'module.__dict__["_tt_diagnostic_console"] = _tt_diagnostic_console'
)
B15_PATH = (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)
LOADER_PATH = "tracktemplate/compatibility/b15_workflow_host.py"


def transform_source(relative, raw):
    """Return the exact predecessor's successor without executing either."""
    _require(relative in SOURCES, "Unlisted diagnostic source")
    binding = SOURCES[relative]
    _require(_identity(raw)["sha256"] == binding["predecessor_sha256"],
             "Diagnostic predecessor source changed")
    tree = ast.parse(raw)
    _require(not any(isinstance(node, ast.Name)
                     and node.id.startswith("_tt_diagnostic")
                     for node in ast.walk(tree)),
             "Diagnostic helper name already exists")
    direct = [site for site in binding["sites"]
              if site[0] != "embedded-raise"]
    after = raw
    # Embedded scripts retain their exact raw literal representation.
    for constant, inner, sites in reversed(_embedded_sites(tree, binding["sites"])):
        before_inner = constant.value.encode()
        after_inner = _wrap_expression(before_inner, inner, sites)
        after_inner = _insert_helpers(after_inner, {"sites": sites})
        start, end = _span(raw, constant)
        literal = raw[start:end]
        _require(literal[:4] in (b'r"""', b"r'''")
                 and literal[-3:] == literal[1:4]
                 and literal[4:-3] == before_inner,
                 "Embedded script raw literal differs")
        after = after[:start] + literal[:4] + after_inner + literal[-3:] + after[end:]
    if direct:
        # Current files have either direct or embedded sites, never both.
        _require(after == raw, "Mixed embedded and direct adaptation differs")
        after = _wrap_expression(raw, tree, direct)
        if relative == LOADER_PATH:
            needle = b'        exec(compile('
            _require(after.count(needle) == 1, "Loader execution site differs")
            after = after.replace(needle, b"        " + LOADER_BINDING.encode()
                                  + b"\n" + needle, 1)
        after = _insert_helpers(after, {"sites": direct})
    verify_equivalence(relative, raw, after)
    return after, {
        "path": relative, "predecessor": _identity(raw),
        "successor": _identity(after),
        "sites": [{"kind": kind, "line": line, "site": site,
                   "expression_sha256": digest}
                  for kind, line, site, _, digest in binding["sites"]],
        "ast_equivalence": "PASS_EXCEPT_EXACT_NAMED_DIAGNOSTIC_EXPRESSIONS",
    }


def _restore_ast(original, changed, sites):
    helper = ast.parse(_helper_source({"sites": sites}))
    helper_dumps = [ast.dump(node, include_attributes=False)
                    for node in helper.body]
    found_helpers = []
    retained = []
    for node in changed.body:
        dumped = ast.dump(node, include_attributes=False)
        if dumped in helper_dumps:
            found_helpers.append(dumped)
        else:
            retained.append(node)
    _require(found_helpers == helper_dumps, "Diagnostic inline helper changed")
    changed.body = retained
    expected = {site: (kind, digest)
                for kind, _, site, _, digest in sites}
    observed = []
    bindings = []
    binding_dump = ast.dump(ast.parse(LOADER_BINDING).body[0],
                            include_attributes=False)

    class Unwrap(ast.NodeTransformer):
        def visit_Assign(self, node):
            if ast.dump(node, include_attributes=False) == binding_dump:
                bindings.append(node)
                return None
            return self.generic_visit(node)

        def visit_Call(self, node):
            if not (isinstance(node.func, ast.Name) and node.func.id in (
                    "_tt_diagnostic_message", "_tt_diagnostic_report",
                    "_tt_diagnostic_b15_tree")):
                return self.generic_visit(node)
            if node.func.id == "_tt_diagnostic_b15_tree":
                site = "b15-compile"
                _require(len(node.args) == 2 and not node.keywords
                         and isinstance(node.args[1], ast.Name)
                         and node.args[1].id == "source",
                         "Diagnostic loader wrapper differs")
                restored = node.args[0]
            else:
                _require(node.args and isinstance(node.args[0], ast.Constant),
                         "Diagnostic wrapper site differs")
                site = node.args[0].value
                _require(site in expected, "Unlisted diagnostic wrapper")
                kind = expected[site][0]
                if kind == "report":
                    _require(node.func.id == "_tt_diagnostic_report",
                             "Diagnostic wrapper kind differs")
                    restored = ast.Call(
                        func=ast.Name(id="print", ctx=ast.Load()),
                        args=node.args[1:], keywords=node.keywords)
                else:
                    _require(node.func.id == "_tt_diagnostic_message"
                             and len(node.args) == 2 and not node.keywords,
                             "Diagnostic message wrapper differs")
                    restored = node.args[1]
            _require(site in expected and site not in observed,
                     "Diagnostic wrapper repeated or unlisted")
            observed.append(site)
            _require(_ast_hash(restored) == expected[site][1],
                     "Original diagnostic expression was changed")
            return restored

    changed = Unwrap().visit(changed)
    _require(len(bindings) == int("b15-compile" in expected),
             "Diagnostic loader helper binding differs")
    _require(set(observed) == set(expected), "Diagnostic site absent")
    _require(ast.dump(original, include_attributes=False)
             == ast.dump(changed, include_attributes=False),
             "Non-diagnostic source semantics changed")
    return True


def verify_equivalence(relative, before, after):
    """Reject AST changes beyond exact helper additions and named wrappers."""
    binding = SOURCES[relative]
    original = ast.parse(before)
    changed = ast.parse(after)
    embedded = _embedded_sites(original, binding["sites"])
    if embedded:
        candidates = [node for node in ast.walk(changed)
                      if isinstance(node, ast.Constant)
                      and isinstance(node.value, str)
                      and "_TT_DIAGNOSTIC_SITES" in node.value]
        _require(len(candidates) == len(embedded),
                 "Embedded diagnostic scripts differ")
        for (former, original_inner, sites), successor in zip(embedded, candidates):
            _restore_ast(original_inner, ast.parse(successor.value), sites)
            successor.value = former.value
        _require(ast.dump(original, include_attributes=False)
                 == ast.dump(changed, include_attributes=False),
                 "Outer source changed beyond embedded diagnostics")
        return True
    return _restore_ast(original, changed, binding["sites"])


def compiled_b15_receipt(raw):
    """Prove the sole derived B15 Console argument before runtime loading."""
    source = raw.decode("utf-8")
    namespace = {}
    exec(_helper_source(SOURCES[LOADER_PATH]), namespace)
    original = ast.parse(source)
    original.body.pop()
    derived = namespace["_tt_diagnostic_b15_tree"](original, source)
    restored = copy.deepcopy(derived)
    calls = [node for node in ast.walk(restored)
             if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name)
             and node.func.id == "_tt_diagnostic_console"]
    _require(len(calls) == 1, "Compiled B15 diagnostic delta differs")
    wrapper = calls[0]
    parent = next(node for node in ast.walk(restored)
                  if isinstance(node, ast.Call) and wrapper in node.args)
    parent.args[parent.args.index(wrapper)] = wrapper.args[1]
    _require(ast.dump(original, include_attributes=False)
             == ast.dump(restored, include_attributes=False),
             "Compiled B15 changed beyond the console argument")
    return {
        "path": B15_PATH, "original_file": _identity(raw),
        "original_ast_without_launch_sha256": _ast_hash(original),
        "derived_compiled_ast_sha256": _ast_hash(derived),
        "site": "CrossoverManagerPanel.preview_geometry:38693",
        "delta": "Wrap only the original App.Console.PrintWarning argument",
        "console_site": "b15-console", "maximum_instances_per_session": 9,
        "original_file_unchanged": True,
        "panel_text_and_original_predicates_unchanged": True,
        "ast_equivalence": "PASS_EXCEPT_EXACT_CONSOLE_ARGUMENT",
    }


def adapt_diagnostics(tree, manifest):
    """Adapt a verified private assessment and return (manifest, receipt).

    All sources are preflighted before the first write. A failed partial
    write remains private evidence and must never be executed or reused.
    Callers must independently review these exact bytes before execution.
    """
    tree = Path(tree).absolute()
    _require(tree.name == "assessment" and ".." not in tree.parts
             and not any(path.is_symlink() for path in (tree, *tree.parents)),
             "Diagnostic target is not an owned assessment directory")
    metadata = tree.stat()
    _require(metadata.st_uid == os.getuid()
             and stat.S_IMODE(metadata.st_mode) == 0o700,
             "Diagnostic assessment is not private and owned")
    assessment.verify_assessment(tree, manifest)
    _require(manifest["base_commit"] == assessment.BASE_COMMIT
             and "diagnostic_successor" not in manifest,
             "Diagnostic assessment predecessor differs")
    changed = copy.deepcopy(manifest)
    rows = {row["path"]: row for row in changed["source_files"]}
    _require(B15_PATH in rows, "Original B15 source is absent")
    b15_bytes = assessment._read_regular(tree / B15_PATH)
    compiled_receipt = compiled_b15_receipt(b15_bytes)
    _require(rows[B15_PATH]["original"] == _identity(b15_bytes)
             and rows[B15_PATH]["assessment"] == _identity(b15_bytes),
             "Original B15 source row differs")
    updates = []
    receipts = []
    differences = []
    for relative, binding in SOURCES.items():
        _require(relative in rows, "Diagnostic assessment source absent")
        row = rows[relative]
        _require(row["original"]["sha256"] == binding["original_sha256"],
                 "Diagnostic original source binding changed")
        path = tree / relative
        _require(path.stat().st_nlink == 1,
                 "Diagnostic assessment source is hard linked")
        before = assessment._read_regular(path)
        after, receipt = transform_source(relative, before)
        updates.append((path, before, after))
        receipts.append(receipt)
        row["assessment"] = _identity(after)
        row["adapted"] = True
        differences.extend(difflib.unified_diff(
            before.decode().splitlines(True), after.decode().splitlines(True),
            fromfile="assessment/" + relative,
            tofile="diagnostic-successor/" + relative))
    diff_path = tree / "_assessment/adaptations.diff"
    diff_before = assessment._read_regular(diff_path)
    diff_after = diff_before + "".join(differences).encode()
    receipt = {
        "schema_version": 1, "status": "PREPARED_NOT_EXECUTED",
        "producer": _identity(Path(__file__).read_bytes()),
        "sources": receipts, "source_count": len(receipts),
        "site_count": sum(len(row["sites"]) for row in receipts),
        "compiled_b15": compiled_receipt,
        "session_environment": SESSION_ENV,
        "private_report_directory": REPORT_DIRECTORY,
        "original_successor_diagnostics_must_be_preserved": True,
        "runtime_admission": False, "zy_execution": False,
    }
    changed["diagnostic_successor"] = receipt
    changed["adaptation_diff"] = _identity(diff_after)
    updates.append((diff_path, diff_before, diff_after))
    manifest_path = tree / "_assessment/manifest.json"
    updates.append((manifest_path, assessment._read_regular(manifest_path),
                    assessment._json_bytes(changed)))
    for path, before, after in updates:
        descriptor = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "r+b") as stream:
            metadata = os.fstat(stream.fileno())
            _require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1
                     and stream.read() == before,
                     "Diagnostic assessment changed during preparation")
            stream.seek(0)
            stream.write(after)
            stream.truncate()
    assessment.verify_assessment(tree, changed)
    return changed, receipt


ENTRY_IDS = frozenset(('straight-generation',
 'native-01',
 'native-02',
 'native-03',
 'native-04',
 'native-05',
 'native-06',
 'native-07',
 'native-08',
 'native-09',
 'native-10',
 'native-11',
 'native-12',
 'native-13',
 'native-14',
 'native-15',
 'native-16',
 'native-17',
 'native-18',
 'native-19',
 'native-20',
 'native-21',
 'native-22',
 'native-23',
 'native-24',
 'native-25',
 'native-26',
 'native-27',
 'native-28',
 'native-29',
 'native-30',
 'native-31',
 'native-32',
 'native-33',
 'native-34',
 'native-35',
 'native-36',
 'native-37',
 'native-38',
 'native-39',
 'native-40',
 'native-41',
 'native-42',
 'native-43',
 'native-44',
 'native-45',
 'native-46',
 'native-47',
 'native-48',
 'native-49',
 'native-50',
 'native-51',
 'native-52',
 'native-53',
 'native-54',
 'native-55',
 'native-56',
 'native-57',
 'phase4-migration',
 'phase3-four-routes',
 'phase5-view-edit-lifecycle',
 'phase7-export-pair',
 'phase8-turnout_toe',
 'phase8-crossover_preflight',
 'phase8-crossover_b4_recovery',
 'phase8-crossover_edit_recovery',
 'phase8-crossover_host_integration_recovery',
 'phase8-turnout_host_integration_recovery',
 'phase8-straight_host_turnout',
 'phase8-straight_host_crossover',
 'phase8-straight_crossover_b4',
 'phase8-turnout-selected-direct',
 'phase8-turnout-selected-main-button',
 'phase8-crossover-selected-highlighted-direct',
 'phase8-crossover-selected-highlighted-main-button',
 'phase8-crossover-selected-preselected-direct',
 'phase8-crossover-selected-preselected-main-button',
 'selected-export-document',
 'selected-export-set',
 'selected-export-rollback',
 'phase3-four-routes-route-1',
 'phase3-four-routes-route-2',
 'phase3-four-routes-route-3',
 'phase3-four-routes-route-4',
 'phase7-export-pair-route-1',
 'phase7-export-pair-route-2'))


REPORTS_BY_ENTRY = {
    "native-24": "n24-report", "native-29": "n29-report",
    "native-30": "n30-report", "native-31": "n31-report",
    "native-49": "n49-report", "native-50": "n50-report",
    "native-51": "n51-report", "native-52": "n52-report",
    "phase5-view-edit-lifecycle": "g05-report",
}
CONSOLE_LIMITS = {
    "phase8-crossover_preflight": (4, 7),
    "phase8-straight_host_crossover": (4, 9),
    "phase8-crossover_edit_recovery": (0, 6),
    "phase8-crossover_b4_recovery": (0, 2),
    "phase8-crossover_host_integration_recovery": (0, 2),
    "phase8-straight_crossover_b4": (0, 2),
    "phase8-crossover-selected-highlighted-direct": (0, 2),
    "phase8-crossover-selected-highlighted-main-button": (0, 2),
    "phase8-crossover-selected-preselected-direct": (0, 2),
    "phase8-crossover-selected-preselected-main-button": (0, 2),
}


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        _require(key not in value, "Diagnostic witness has duplicate fields")
        value[key] = item
    return value


def verify_private_reports(session, entry_id, public_texts, *, completed):
    """Match every emitted witness to its exact owned private original.

    Call after each session and again before sealing. Supply original
    stdout/stderr channels without transformations. The private sidecar
    binds each original independently of the native Console display sink.
    Visible witnesses must match it. Successful sources require their exact
    report/console counts and the original print-report sentinel. Missing
    originals, sidecars, extra members, links and drift fail closed. Neither
    original report bytes nor the private sidecar enter public artifacts.
    """
    _require(type(completed) is bool and type(entry_id) is str
             and entry_id in ENTRY_IDS
             and type(public_texts) in (list, tuple)
             and all(type(text) is str for text in public_texts),
             "Diagnostic verification argument types differ")
    session = Path(session).absolute()
    _require(".." not in session.parts and session.is_dir()
             and not any(path.is_symlink()
                         for path in (session, *session.parents))
             and session.stat().st_uid == os.getuid()
             and stat.S_IMODE(session.stat().st_mode) == 0o700,
             "Diagnostic verification session differs")
    report_site = REPORTS_BY_ENTRY.get(entry_id)
    expected_console, console_limit = CONSOLE_LIMITS.get(entry_id, (0, 0))
    def validate_witness(witness):
        _require(type(witness) is dict, "Diagnostic witness type differs")
        site = witness.get("site")
        console = site == "b15-console"
        fields = {"site", "bytes", "sha256"}
        if console:
            fields.add("instance")
        _require(set(witness) == fields and type(site) is str
                 and (console and console_limit or site == report_site)
                 and type(witness["bytes"]) is int
                 and 0 <= witness["bytes"] <= 64 * 1024 * 1024
                 and type(witness["sha256"]) is str
                 and len(witness["sha256"]) == 64
                 and all(char in "0123456789abcdef"
                         for char in witness["sha256"]),
                 "Diagnostic witness fields differ")
        if console:
            instance = witness["instance"]
            _require(type(instance) is int and 1 <= instance <= console_limit,
                     "Diagnostic console instance differs")
            return "b15-console-%04d.txt" % instance
        return site + ".txt"

    witnesses = {}
    sidecar = session / "diagnostic-witnesses.jsonl"
    if sidecar.exists() or sidecar.is_symlink():
        _require(not sidecar.is_symlink(), "Diagnostic witness sidecar is linked")
        metadata = sidecar.stat()
        _require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1
                 and metadata.st_uid == os.getuid()
                 and stat.S_IMODE(metadata.st_mode) == 0o600
                 and 0 < metadata.st_size <= 16384,
                 "Diagnostic witness sidecar type or mode differs")
        sidecar_raw = assessment._read_regular(sidecar)
        _require(sidecar_raw.endswith(b"\n"), "Diagnostic witness is incomplete")
        for line in sidecar_raw.decode("utf-8").splitlines():
            witness = json.loads(line, object_pairs_hook=_unique_object)
            name = validate_witness(witness)
            _require(name not in witnesses, "Diagnostic sidecar witness repeated")
            witnesses[name] = witness
    emitted = set()
    for text in public_texts:
        for line in text.splitlines():
            markers = [marker for marker in (
                REPORT_MARKER, "TRACKTEMPLATE_PHASE5_VIEWPROVIDER_GUI=")
                if marker in line]
            if not markers:
                continue
            _require(len(markers) == 1, "Diagnostic witness marker repeated")
            marker = markers[0]
            _require(line.count(marker) == 1,
                     "Diagnostic witness marker repeated")
            raw = line.split(marker, 1)[1]
            witness = json.loads(raw, object_pairs_hook=_unique_object)
            name = validate_witness(witness)
            _require(name not in emitted and witnesses.get(name) == witness,
                     "Emitted diagnostic witness differs from private sidecar")
            emitted.add(name)
    directory = session / REPORT_DIRECTORY
    members = {}
    if directory.exists() or directory.is_symlink():
        _require(not directory.is_symlink() and directory.is_dir()
                 and directory.stat().st_uid == os.getuid()
                 and stat.S_IMODE(directory.stat().st_mode) == 0o700,
                 "Diagnostic private directory differs")
        for path in directory.iterdir():
            _require(path.name in witnesses and not path.is_symlink(),
                     "Unlisted diagnostic private member")
            metadata = path.stat()
            _require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1
                     and metadata.st_uid == os.getuid()
                     and stat.S_IMODE(metadata.st_mode) == 0o600
                     and metadata.st_size <= 64 * 1024 * 1024,
                     "Diagnostic private member type or mode differs")
            identity = _identity(assessment._read_regular(path))
            _require(identity == {key: witnesses[path.name][key]
                                  for key in ("bytes", "sha256")},
                     "Diagnostic private original differs from witness")
            members[path.name] = identity
    _require(set(members) == set(witnesses),
             "Diagnostic private original is missing")
    console_names = sorted(name for name in members
                           if name.startswith("b15-console-"))
    _require(console_names == ["b15-console-%04d.txt" % number
                               for number in range(1, len(console_names) + 1)],
             "Diagnostic console occurrence sequence differs")
    if completed:
        _require((report_site is None or report_site + ".txt" in emitted)
                 and len(console_names) == expected_console,
                 "Completed source lacks required original diagnostic reports")
    return {"status": "PASS", "entry_id": entry_id,
            "completed": completed, "members": members,
            "console_instances": len(console_names)}
