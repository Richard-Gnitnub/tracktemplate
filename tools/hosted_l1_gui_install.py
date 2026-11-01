"""Bound the hosted GUI installer and prove its owned process cleanup.

This module never runs FreeCAD. The system service runs as the non-root
runner; only the retained OS installation commands use sudo.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time
import traceback

from tools import freecad_validation_guard as guard


ROOT = Path(__file__).resolve().parents[1]
CGROUP_ROOT = Path('/sys/fs/cgroup')
RUNTIME_SECONDS = 570
STOP_SECONDS = 5
INSTALL_SCRIPT = '''#!/bin/bash
set -euo pipefail
umask 077
ulimit -c 0
test "$(id -u)" -ne 0
apt_options=(-o Acquire::Retries=0 -o Acquire::http::Timeout=15 -o Acquire::https::Timeout=15)
sudo -n apt-get "${apt_options[@]}" update --error-on=any
sudo -n apt-get "${apt_options[@]}" install --no-install-recommends -y flatpak dbus-user-session xvfb xauth
sudo -n flatpak remote-add --system --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
sudo -n flatpak install --system --noninteractive -y flathub app/org.freecad.FreeCAD/x86_64/stable runtime/org.kde.Platform/x86_64/6.11
sudo -n flatpak update --system --noninteractive -y --no-related --no-deps --commit=e63d66825c4daf9adb09283488c2bc2ace92ed8b24bcf81666933226ed082fd4 app/org.freecad.FreeCAD/x86_64/stable
sudo -n flatpak update --system --noninteractive -y --no-related --no-deps --commit=fe192771c0992ad873e6a9ccc6e4f087c76314ce5ced165650cc7ea045a6bbaa runtime/org.kde.Platform/x86_64/6.11
pilot_uid="$(id -u)"
pilot_manager="user@${pilot_uid}.service"
pilot_group="/user.slice/user-${pilot_uid}.slice/${pilot_manager}"
sudo -n loginctl enable-linger "$(id -un)"
sudo -n systemctl start "$pilot_manager"
systemctl show "$pilot_manager" -p ActiveState -p ControlGroup -p Delegate -p DelegateControllers
test "$(systemctl show "$pilot_manager" -p ActiveState --value)" = active
test "$(systemctl show "$pilot_manager" -p ControlGroup --value)" = "$pilot_group"
test "$(systemctl show "$pilot_manager" -p Delegate --value)" = yes
pilot_delegated="$(systemctl show "$pilot_manager" -p DelegateControllers --value)"
pilot_available="$(cat "/sys/fs/cgroup${pilot_group}/cgroup.controllers")"
printf 'Delegated controllers: %s\\nAvailable controllers: %s\\n' "$pilot_delegated" "$pilot_available"
for pilot_controller in cpu memory pids; do
  case " $pilot_delegated " in
    *" $pilot_controller "*) ;;
    *) echo "Required delegation missing: $pilot_controller" >&2; exit 1 ;;
  esac
  case " $pilot_available " in
    *" $pilot_controller "*) ;;
    *) echo "Required kernel controller missing: $pilot_controller" >&2; exit 1 ;;
  esac
done
test ! -e /home/richard
sudo -n install -d -m 700 -o "$(id -u)" -g "$(id -g)" /home/richard
'''

SHOW_FIELDS = (
    'Id', 'LoadState', 'InvocationID', 'ControlGroup', 'MainPID',
    'ControlPID', 'ActiveState', 'SubState', 'ExecMainCode',
    'ExecMainStatus', 'ExecMainExitTimestampMonotonic', 'Result',
    'User', 'Group', 'RuntimeMaxUSec', 'TimeoutStopUSec', 'KillMode',
    'Restart', 'SendSIGKILL', 'Type', 'RemainAfterExit', 'ExecStart',
)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _regular(path):
    _require(not any(item.is_symlink() for item in (path, *path.parents))
             and path.is_file() and path.stat().st_uid == os.getuid(),
             'Installer evidence identity differs')


def _write(path, record):
    # Exclusive files preserve the original evidence on repeated entry.
    with path.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, sort_keys=True, indent=2)
        stream.write('\n')


def _identity(work):
    _require(os.getuid() != 0, 'Installer coordinator must be non-root')
    _require(os.environ.get('GITHUB_ACTIONS') == 'true'
             and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
             and os.environ.get('GITHUB_RUN_ATTEMPT') == '1',
             'Hosted first-attempt installer required')
    run_id = os.environ.get('GITHUB_RUN_ID', '')
    source = os.environ.get('GITHUB_SHA', '')
    _require(re.fullmatch(r'[1-9][0-9]*', run_id)
             and re.fullmatch(r'[0-9a-f]{40}', source),
             'Installer run or source identity absent')
    expected = Path(os.environ['RUNNER_TEMP']) / ('l1-gui-' + run_id)
    _require(work == expected and work.is_absolute()
             and not any(item.is_symlink() for item in (work, *work.parents))
             and work.is_dir() and (work / 'evidence').is_dir()
             and not (work / 'evidence').is_symlink()
             and work.stat().st_uid == os.getuid(),
             'Installer workspace differs')
    return {
        'schema': 1, 'run_id': int(run_id), 'source_commit': source,
        'unit': 'tracktemplate-l1-install-' + run_id + '.service',
        'uid': os.getuid(), 'gid': os.getgid(),
        'module_sha256': _digest(Path(__file__)),
        'script_sha256': hashlib.sha256(INSTALL_SCRIPT.encode()).hexdigest(),
        'command': ['/bin/bash', str(work / 'installer.sh')],
        'runtime_seconds': RUNTIME_SECONDS, 'stop_seconds': STOP_SECONDS,
    }


def _command(arguments, deadline, *, check=True, timeout=5):
    remaining = deadline - time.monotonic()
    _require(remaining > 0, 'Installer command deadline expired')
    return subprocess.run(arguments, check=check, capture_output=True,
                          text=True, timeout=min(timeout, remaining))


def _show(unit, deadline):
    arguments = ['systemctl', 'show', unit]
    for name in SHOW_FIELDS:
        arguments.extend(['-p', name])
    result = _command(arguments, deadline, check=False)
    _require(result.returncode in (0, 4), 'Installer unit query failed')
    rows = [line.split('=', 1) for line in result.stdout.splitlines()]
    _require(all(len(row) == 2 for row in rows)
             and len({row[0] for row in rows}) == len(rows),
             'Malformed installer unit query')
    return dict(rows)


def _absent(shown, unit):
    return all(shown.get(name) == value for name, value in {
        'Id': unit, 'LoadState': 'not-found', 'ActiveState': 'inactive',
        'SubState': 'dead', 'MainPID': '0', 'ControlPID': '0',
        'ControlGroup': '', 'InvocationID': '',
    }.items())


def _owned(shown, intent, owner=None):
    unit = intent['unit']
    expected = {
        'Id': unit, 'User': str(intent['uid']), 'Group': str(intent['gid']),
        'ControlGroup': '/system.slice/' + unit,
        'KillMode': 'control-group', 'Restart': 'no',
        'SendSIGKILL': 'yes', 'Type': 'exec', 'RemainAfterExit': 'yes',
    }
    exit_time = shown.get('ExecMainExitTimestampMonotonic')
    # RemainAfterExit can keep a completed service active after systemd
    # releases its cgroup. This still needs the retained exact owner below.
    successful_exit = (
        shown.get('ActiveState') == 'active'
        and shown.get('SubState') == 'exited'
        and shown.get('ExecMainCode') == '1'
        and shown.get('ExecMainStatus') == '0'
        and shown.get('Result') == 'success'
        and isinstance(exit_time, str)
        and re.fullmatch(r'[1-9][0-9]*', exit_time)
    )
    stopped_group = (owner is not None
                     and shown.get('ControlGroup') == ''
                     and (shown.get('ActiveState') in ('inactive', 'failed')
                          or successful_exit)
                     and shown.get('MainPID') == '0'
                     and shown.get('ControlPID') == '0')
    _require(all(shown.get(name) == value
                 or (name == 'ControlGroup' and stopped_group)
                 for name, value in expected.items()),
             'Installer unit identity or safety properties differ')
    _require(shown.get('RuntimeMaxUSec') in ('9min 30s', '570000000')
             and shown.get('TimeoutStopUSec') in ('5s', '5000000'),
             'Installer kernel deadlines differ')
    invocation = shown.get('InvocationID', '')
    _require(re.fullmatch(r'[0-9a-f]{32}', invocation),
             'Installer invocation absent')
    match = re.search(r'argv\[\]=(.*?)\s*;', shown.get('ExecStart', ''))
    _require(match and shlex.split(match[1]) == intent['command'],
             'Installer command differs')
    if owner is not None:
        _require(owner == {'intent': intent, 'invocation': invocation,
                           'cgroup': expected['ControlGroup']},
                 'Installer ownership changed')
    return {'intent': intent, 'invocation': invocation,
            'cgroup': expected['ControlGroup']}


def _sample(group):
    sample = guard._sample(group)
    _require(all(value is not None for value in sample.values()),
             'Installer resource telemetry incomplete')
    for name in ('memory.current', 'memory.peak', 'memory.swap.current',
                 'pids.current'):
        _require(int(sample[name]) >= 0, 'Invalid installer resource sample')
    cpu = dict(line.split() for line in sample['cpu.stat'].splitlines())
    _require(int(cpu['usage_usec']) >= 0, 'Invalid installer CPU sample')
    sample['monotonic_seconds'] = time.monotonic()
    return sample


def _empty(group):
    if not group.exists():
        return True
    return (guard._empty(group)
            and (group / 'cgroup.procs').read_text().strip() == ''
            and (group / 'pids.current').read_text().strip() == '0')


def cleanup(work, *, deadline=None):
    """Recheck ownership, stop only that unit and prove no owned processes."""
    deadline = time.monotonic() + 15 if deadline is None else deadline
    result = {'cleanup': False, 'errors': [], 'observations': []}
    try:
        intent = _identity(work)
        for name in ('installer-intent.json', 'installer-ownership.json'):
            _regular(work / 'evidence' / name)
        _regular(work / 'installer.sh')
        _require(_digest(work / 'installer.sh') == intent['script_sha256'],
                 'Installer script changed')
        saved = json.loads((work / 'evidence/installer-intent.json').read_text())
        _require(saved == intent, 'Installer intent differs')
        owner = json.loads((work / 'evidence/installer-ownership.json').read_text())
        _require(owner.get('intent') == intent
                 and owner.get('cgroup') == '/system.slice/' + intent['unit']
                 and re.fullmatch(r'[0-9a-f]{32}', owner.get('invocation', '')),
                 'Malformed installer ownership')
        group = CGROUP_ROOT / owner['cgroup'].lstrip('/')
        shown = _show(intent['unit'], deadline)
        result['observations'].append(shown)
        if not _absent(shown, intent['unit']):
            _owned(shown, intent, owner)
            _command(['sudo', '-n', 'systemctl', 'stop', intent['unit']],
                     deadline, timeout=STOP_SECONDS + 2)
        while True:
            shown = _show(intent['unit'], deadline)
            result['observations'].append(shown)
            if _absent(shown, intent['unit']):
                stopped = True
            else:
                _owned(shown, intent, owner)
                stopped = (shown.get('ActiveState') in ('inactive', 'failed')
                           and shown.get('MainPID') == '0'
                           and shown.get('ControlPID') == '0')
            if stopped and _empty(group):
                result.update(cleanup=True, cgroup_removed=not group.exists(),
                              owned_invocation=owner['invocation'])
                break
            _require(time.monotonic() < deadline,
                     'Installer processes remain or cleanup timed out')
            time.sleep(min(0.1, max(0, deadline - time.monotonic())))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        result['errors'].append(traceback.format_exc())
    return result


def run(work):
    """Run installation once; preserve failure, measurements and cleanup."""
    started = time.monotonic()
    # Leave the outer 600-second step time to flush receipts and return.
    operation_deadline, cleanup_deadline = started + 575, started + 595
    result = {'schema': 1, 'status': 'FAIL', 'cleanup': False, 'errors': [],
              'exit_status': None, 'resources': {},
              'started_monotonic_seconds': started}
    samples = []
    owner = None
    validated = False
    try:
        intent = _identity(work)
        validated = True
        _require(_absent(_show(intent['unit'], operation_deadline),
                         intent['unit']), 'Installer unit already exists')
        _write(work / 'evidence/installer-intent.json', intent)
        with (work / 'installer.sh').open('x', encoding='utf-8') as stream:
            stream.write(INSTALL_SCRIPT)
        output = work / 'evidence/installer-output.log'
        with output.open('x', encoding='utf-8'):
            pass
        properties = {
            'User': str(os.getuid()), 'Group': str(os.getgid()),
            'Type': 'exec', 'RemainAfterExit': 'yes',
            'RuntimeMaxSec': str(RUNTIME_SECONDS),
            'TimeoutStopSec': str(STOP_SECONDS),
            'KillMode': 'control-group', 'SendSIGKILL': 'yes',
            'Restart': 'no', 'LimitCORE': '0',
            'CPUAccounting': 'yes', 'MemoryAccounting': 'yes',
            'TasksAccounting': 'yes', 'WorkingDirectory': str(ROOT),
            'StandardOutput': 'append:' + str(output),
            'StandardError': 'inherit',
        }
        arguments = ['sudo', '-n', 'systemd-run', '--quiet',
                     '--unit=' + intent['unit']]
        arguments.extend('--property=' + key + '=' + value
                         for key, value in properties.items())
        arguments.extend(intent['command'])
        result['launch_command'] = arguments
        _command(arguments, operation_deadline)
        shown = _show(intent['unit'], operation_deadline)
        owner = _owned(shown, intent)
        _write(work / 'evidence/installer-ownership.json', owner)
        group = CGROUP_ROOT / owner['cgroup'].lstrip('/')
        while True:
            _owned(shown, intent, owner)
            terminated = int(shown['ExecMainExitTimestampMonotonic']) > 0
            if terminated:
                result.update(exit_status=int(shown['ExecMainStatus']),
                              terminal_unit=shown)
            # A failed service can already have released its cgroup. Keep
            # its exit status and prior measurements; absence is no sample.
            if group.exists():
                samples.append(_sample(group))
            else:
                _require(terminated, 'Live installer cgroup disappeared')
            if terminated:
                _require(shown['ExecMainCode'] == '1'
                         and result['exit_status'] == 0
                         and shown['Result'] == 'success',
                         'Installer command failed or exceeded its deadline')
                _require(samples, 'Installer resource measurements absent')
                result['status'] = 'PASS'
                break
            _require(time.monotonic() < operation_deadline,
                     'Installer observation deadline expired')
            time.sleep(min(0.5, max(0, operation_deadline - time.monotonic())))
            shown = _show(intent['unit'], operation_deadline)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        result['errors'].append(traceback.format_exc())
    finally:
        if owner is not None:
            receipt = cleanup(work, deadline=cleanup_deadline)
            result.update(cleanup=receipt['cleanup'], finalization=receipt)
        if samples:
            result['resources'] = {
                'memory_peak_bytes': max(int(row['memory.peak'])
                                         for row in samples),
                'cpu_usage_usec': max(int(dict(line.split() for line in
                                              row['cpu.stat'].splitlines())
                                         ['usage_usec']) for row in samples),
                'tasks_peak': max(int(row['pids.current']) for row in samples),
                'samples': len(samples), 'accounting': 'sampled-lower-bound',
            }
        if result['errors'] or not result['cleanup']:
            result['status'] = 'FAIL'
        if result['status'] == 'PASS':
            try:
                # The service does not inherit workflow credentials. Export
                # only the values needed by later non-root GUI stages.
                with Path(os.environ['GITHUB_ENV']).open(
                        'a', encoding='utf-8') as stream:
                    stream.write(f'XDG_RUNTIME_DIR=/run/user/{os.getuid()}\n')
                    stream.write('DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/'
                                 f'{os.getuid()}/bus\n')
            except (OSError, KeyError):
                result['errors'].append(traceback.format_exc())
                result['status'] = 'FAIL'
        result['elapsed_seconds'] = time.monotonic() - started
        result['samples'] = samples
        if validated:
            _write(work / 'evidence/installer-result.json', result)
    return 0 if result['status'] == 'PASS' else 1
