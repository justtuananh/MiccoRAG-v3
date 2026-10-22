#!/usr/bin/env python3
"""Exec the reviewed Vite command with a protected snapshot of its environment."""
import argparse
import json
import os
import stat
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--node', type=Path, required=True)
    parser.add_argument('--vite', type=Path, required=True)
    parser.add_argument('--host', choices=('0.0.0.0', '127.0.0.1'), required=True)
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()
    if args.port != 5174:
        parser.error('Only the reviewed frontend port is permitted')
    if args.config.is_symlink():
        parser.error('Environment file must not be a symlink')
    info = args.config.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        parser.error('Environment file must be owned by this user with mode 0600')
    environment = json.loads(args.config.read_text())
    if not isinstance(environment, dict) or any(
        not isinstance(key, str) or not isinstance(value, str) or not key
        or '=' in key or '\0' in key or '\0' in value
        for key, value in environment.items()
    ):
        parser.error('Environment file must contain string environment values')
    os.environ.update(environment)
    os.execv(str(args.node), [str(args.node), str(args.vite), '--host', args.host,
                              '--port', str(args.port)])


if __name__ == '__main__':
    main()
