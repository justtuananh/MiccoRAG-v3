#!/usr/bin/env python3
"""One-shot, unprivileged watchdog for the owned miccoRAG backend and Vite UI.

Cron runs this at boot and every minute. It never terminates a process. A
protected maintenance marker suspends spawning while a deployment owns startup.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import socket
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ServiceSpec:
    name: str
    cwd: Path
    port: int
    command: tuple[str, ...]
    expected_tokens: tuple[str, ...]
    health_path: str
    log_path: Path | None = None
    process_executable: str | None = None  # Exec runners may replace themselves.


def protected_file(path: Path) -> None:
    if path.is_symlink():
        raise ValueError('Protected configuration must not be a symlink')
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('Protected configuration must be owned by this user with mode 0600')


def private_dir(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.stat()
    if path.is_symlink() or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('Supervisor state directory must be private and owned by this user')


def _listen_inodes(port: int) -> set[str]:
    inodes = set()
    for table in ('/proc/net/tcp', '/proc/net/tcp6'):
        try:
            lines = Path(table).read_text().splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            columns = line.split()
            if len(columns) > 9 and columns[3] == '0A' and int(columns[1].split(':')[1], 16) == port:
                inodes.add(columns[9])
    return inodes


def listener_pids(port: int) -> set[int]:
    inodes = _listen_inodes(port)
    if not inodes:
        return set()
    wanted = {'socket:[' + inode + ']' for inode in inodes}
    found = set()
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            if proc.stat().st_uid != os.getuid():
                continue
            for fd in (proc / 'fd').iterdir():
                try:
                    if os.readlink(fd) in wanted:
                        found.add(int(proc.name))
                        break
                except OSError:
                    continue
        except OSError:
            continue
    return found


def process_matches(pid: int, service: ServiceSpec) -> bool:
    proc = Path('/proc') / str(pid)
    try:
        if proc.stat().st_uid != os.getuid() or Path(os.readlink(proc / 'cwd')) != service.cwd:
            return False
        executable = Path(os.readlink(proc / 'exe')).resolve()
        if executable != Path(service.process_executable or service.command[0]).resolve():
            return False
        argv = (proc / 'cmdline').read_bytes().decode(errors='replace').split('\0')
        command_line = ' '.join(argv)
        return all(token in command_line for token in service.expected_tokens)
    except OSError:
        return False


def healthy(port: int, path: str) -> bool:
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}{path}', timeout=2) as response:
            return response.status == 200
    except (OSError, urllib.error.HTTPError):
        return False


def _atomic_json(path: Path, payload: dict) -> None:
    temp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    fd = os.open(temp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(payload, stream, sort_keys=True)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def reconcile(service: ServiceSpec, previous: dict | None, maintenance: bool) -> dict:
    listeners = listener_pids(service.port)
    if listeners:
        matched = sorted(pid for pid in listeners if process_matches(pid, service))
        if not matched:
            return {'status': 'blocked-unowned-listener', 'port': service.port}
        pid = matched[0]
        return {'status': 'healthy' if healthy(service.port, service.health_path) else 'unhealthy',
                'pid': pid, 'port': service.port, 'adopted': True}
    if _listen_inodes(service.port):
        return {'status': 'blocked-unowned-listener', 'port': service.port}
    if maintenance:
        return {'status': 'maintenance', 'port': service.port}
    previous_pid = (previous or {}).get('pid')
    if isinstance(previous_pid, int) and process_matches(previous_pid, service):
        return {'status': 'starting', 'pid': previous_pid, 'port': service.port}
    log_fd = None
    if service.log_path is not None:
        private_dir(service.log_path.parent)
        if service.log_path.is_symlink():
            raise ValueError('Application log must not be a symlink')
        log_fd = os.open(service.log_path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
        info = os.fstat(log_fd)
        if info.st_uid != os.getuid() or info.st_mode & 0o077:
            os.close(log_fd)
            raise ValueError('Application log must be private and owned by this user')
    try:
        child = subprocess.Popen(service.command, cwd=service.cwd, stdin=subprocess.DEVNULL,
                                 stdout=log_fd if log_fd is not None else subprocess.DEVNULL,
                                 stderr=log_fd if log_fd is not None else subprocess.DEVNULL,
                                 start_new_session=True, close_fds=True)
    finally:
        if log_fd is not None:
            os.close(log_fd)
    return {'status': 'spawned', 'pid': child.pid, 'port': service.port}


def run_once(services: tuple[ServiceSpec, ...], state_dir: Path,
             maintenance_marker: Path) -> dict:
    private_dir(state_dir)
    lock_path = state_dir / 'watchdog.lock'
    if lock_path.is_symlink():
        raise ValueError('Supervisor lock must not be a symlink')
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        info = os.fstat(lock_fd)
        if info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('Supervisor lock is not private')
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'another-run-active'}
        state_path = state_dir / 'state.json'
        if state_path.exists():
            protected_file(state_path)
            previous = json.loads(state_path.read_text())
        else:
            previous = {}
        maintenance = maintenance_marker.exists()
        results = {service.name: reconcile(service, previous.get(service.name), maintenance)
                   for service in services}
        _atomic_json(state_path, results)
        return results
    finally:
        os.close(lock_fd)


def load_production_config(path: Path) -> tuple[tuple[ServiceSpec, ...], Path, Path]:
    protected_file(path)
    config = json.loads(path.read_text())
    root = Path(config['project_root']).resolve()
    backend = root / 'micco-backend' / 'backend'
    frontend = root / 'micco-frontend'
    if not root.is_absolute() or backend.resolve() != backend or frontend.resolve() != frontend:
        raise ValueError('Project directories must be absolute and symlink-free')
    for cwd in (backend, frontend):
        if not cwd.is_dir() or cwd.stat().st_uid != os.getuid():
            raise ValueError('Project directories must exist and be owned by the service user')
    # Keep the configured venv entrypoint: resolving its symlink to /usr/bin/python
    # would discard the venv's site-packages when cron starts the backend.
    python = Path(config['python'])
    node = Path(config['node'])
    if not python.is_absolute() or not node.is_absolute():
        raise ValueError('Runtime executables must be absolute paths')
    backend_env = Path(config['backend_env'])
    frontend_env = Path(config['frontend_env'])
    if not backend_env.is_absolute() or not frontend_env.is_absolute():
        raise ValueError('Environment paths must be absolute')
    protected_file(backend_env)
    protected_file(frontend_env)
    runner = root / 'harness' / 'ops' / 'run_backend.py'
    frontend_runner = root / 'harness' / 'ops' / 'run_frontend.py'
    vite = frontend / 'node_modules' / 'vite' / 'bin' / 'vite.js'
    for executable in (python, node, runner, frontend_runner, vite):
        if not executable.is_file():
            raise ValueError('Required runtime executable is missing')
    frontend_host = config['frontend_host']
    if frontend_host not in ('0.0.0.0', '127.0.0.1'):
        raise ValueError('Frontend host must be an explicit reviewed bind address')
    state_dir = Path(config['state_dir'])
    log_dir = Path(config['log_dir'])
    if not state_dir.is_absolute() or not log_dir.is_absolute():
        raise ValueError('State and log directories must be absolute')
    marker = state_dir / 'deploy-maintenance'
    services = (
        ServiceSpec('backend', backend, 8001,
                    (str(python), str(runner), '--config', str(backend_env), '--port', '8001'),
                    ('uvicorn', 'app.main:app', '8001'), '/ready', log_dir / 'backend.log'),
        ServiceSpec('frontend', frontend, 5174,
                    (str(python), str(frontend_runner), '--config', str(frontend_env),
                     '--node', str(node), '--vite', str(vite), '--host', frontend_host,
                     '--port', '5174'),
                    ('node_modules/vite/bin/vite.js', '--host', frontend_host,
                    '--port', '5174'), '/', log_dir / 'frontend.log', str(node)),
    )
    return services, state_dir, marker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--check-config', action='store_true',
                        help='Validate paths, ownership, modes and live process adoption without spawning')
    args = parser.parse_args()
    services, state_dir, marker = load_production_config(args.config)
    if args.check_config:
        result = {}
        for service in services:
            pids = listener_pids(service.port)
            adoptable = bool(pids) and all(process_matches(pid, service) for pid in pids)
            if pids and not adoptable:
                raise ValueError(f'Existing {service.name} listener does not match reviewed runtime')
            result[service.name] = {'port': service.port, 'listener_count': len(pids),
                                    'adoptable': adoptable}
        print(json.dumps({'validated': True, 'services': result}, sort_keys=True))
        return
    result = run_once(services, state_dir, marker)
    print(json.dumps(result, sort_keys=True))  # IDs/status only; no runtime env values.


if __name__ == '__main__':
    main()
