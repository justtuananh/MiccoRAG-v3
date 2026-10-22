#!/usr/bin/env python3
"""MiccoRAG quiesced backup and staging-only restore rehearsal.

No production restore command exists. This script never starts/stops services.
Run with a separately mounted backup destination and a staged PostgreSQL
container labelled `miccorag.rehearsal=true`.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tarfile

PG_CONTAINER = "nexusrag-postgres"
CHROMA_CONTAINER = "nexusrag-chromadb"
BACKUP_PREFIX = "miccorag-"
STAGE_LABEL = "miccorag.rehearsal=true"
DB_NAME = "nexusrag"
DB_USER = "postgres"


class GuardError(RuntimeError):
    pass


def run(args: list[str], *, input_file=None) -> bytes:
    try:
        result = subprocess.run(args, stdin=input_file, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, check=False)
    except OSError as error:
        raise GuardError(f"Required command unavailable: {args[0]}") from error
    if result.returncode:
        raise GuardError(f"Command failed (exit {result.returncode}): {args[0]} {args[1] if len(args)>1 else ''}")
    return result.stdout


def docker_running(name: str) -> bool:
    return run(["docker", "inspect", "--format", "{{.State.Running}}", name]).strip() == b"true"


def assert_ports_quiet(ports: list[int]) -> None:
    for port in ports:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                raise GuardError(f"Backend port {port} is still listening; stop MiccoRAG writes first")


def assert_backup_sources(paths: dict[str, Path]) -> None:
    for label, path in paths.items():
        if not path.is_absolute() or not path.is_dir() or path.is_symlink():
            raise GuardError(f"{label} must be an existing absolute directory without a symlink")
        for root, dirs, files in os.walk(path):
            for name in dirs + files:
                if (Path(root) / name).is_symlink():
                    raise GuardError(f"{label} contains a symlink; inspect before backing up")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def archive_files(path: Path, target: Path, label: str) -> None:
    with tarfile.open(target, "w:gz") as tar:
        tar.add(path, arcname=label, recursive=True)


def destination_guard(path: Path, allow_local: bool) -> Path:
    path = path.resolve(strict=True)
    if not path.is_dir() or path == Path("/"):
        raise GuardError("Backup destination must be an existing directory")
    if not allow_local and not os.path.ismount(path):
        raise GuardError("Backup destination must be a separately mounted path; use --allow-local only for isolated tests")
    return path


def backup(args: argparse.Namespace) -> Path:
    destination = destination_guard(args.destination, args.allow_local)
    sources = {"uploads": args.uploads.resolve(), "knowledge_graph": args.knowledge_graph.resolve(),
               "chroma": args.chroma.resolve(), "config": args.config.resolve()}
    assert_backup_sources(sources)
    if any(destination == path or destination.is_relative_to(path) for path in sources.values()):
        raise GuardError("Backup destination must be outside all backed-up paths")
    assert_ports_quiet(args.backend_port)
    if not docker_running(PG_CONTAINER):
        raise GuardError("MiccoRAG PostgreSQL must be running for pg_dump")
    if docker_running(CHROMA_CONTAINER):
        raise GuardError("Stop nexusrag-chromadb before copying its index volume")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = destination / f"{BACKUP_PREFIX}{stamp}"
    out.mkdir(mode=0o700)
    try:
        dump = out / "database.dump"
        with dump.open("wb") as stream:
            process = subprocess.run(["docker", "exec", PG_CONTAINER, "pg_dump", "-U", DB_USER,
                                      "-d", DB_NAME, "-Fc"], stdout=stream,
                                     stderr=subprocess.PIPE, check=False)
        if process.returncode or dump.stat().st_size == 0:
            raise GuardError("pg_dump failed or produced an empty archive")
        os.chmod(dump, 0o600)
        archive = out / "files.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            for label, source in sources.items():
                tar.add(source, arcname=label, recursive=True)
        os.chmod(archive, 0o600)
        manifest = {"format": 1, "created_utc": stamp, "database": DB_NAME,
                    "sha256": {dump.name: sha256(dump), archive.name: sha256(archive)},
                    "source_labels": sorted(sources), "off_host_copy_verified": False}
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        os.chmod(out / "manifest.json", 0o600)
        (out / "COMPLETE").write_text("verified snapshot artifacts\n")
        os.chmod(out / "COMPLETE", 0o600)
    except BaseException:
        shutil.rmtree(out)
        raise
    prune(destination, args.retention_days)
    return out


def prune(destination: Path, retention_days: int) -> None:
    if retention_days < 30:
        raise GuardError("Retention must be at least 30 days")
    now = datetime.now(timezone.utc)
    for path in destination.glob(f"{BACKUP_PREFIX}*"):
        if not path.is_dir() or path.is_symlink() or not (path / "COMPLETE").is_file():
            continue
        match = re.fullmatch(r"miccorag-(\d{8}T\d{6}Z)", path.name)
        if not match:
            continue
        created = datetime.strptime(match.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        if (now - created).days > retention_days:
            shutil.rmtree(path)


def verify_backup(path: Path) -> dict:
    if not path.is_dir() or path.is_symlink() or not (path / "COMPLETE").is_file():
        raise GuardError("Incomplete or missing backup")
    manifest = json.loads((path / "manifest.json").read_text())
    if manifest.get("format") != 1 or manifest.get("database") != DB_NAME:
        raise GuardError("Unsupported backup manifest")
    for name in ("database.dump", "files.tar.gz"):
        expected = manifest.get("sha256", {}).get(name)
        if not expected or sha256(path / name) != expected:
            raise GuardError(f"Checksum mismatch: {name}")
    with tarfile.open(path / "files.tar.gz") as tar:
        for item in tar:
            parts = Path(item.name).parts
            if (not parts or parts[0] not in {"uploads", "knowledge_graph", "chroma", "config"}
                    or ".." in parts or item.name.startswith("/")
                    or not (item.isfile() or item.isdir())):
                raise GuardError("Unsafe or unexpected file in archive")
    return manifest


def stage_guard(path: Path, container: str, database: str) -> None:
    if path.exists() or not path.is_absolute() or "stage" not in path.name.lower():
        raise GuardError("Stage target must be a new absolute path with 'stage' in its name")
    if not re.fullmatch(r"[a-z][a-z0-9_]*stage[a-z0-9_]*", database):
        raise GuardError("Staging database name must contain 'stage' and use safe identifiers")
    if container in {PG_CONTAINER, CHROMA_CONTAINER} or "stage" not in container.lower():
        raise GuardError("Production containers are forbidden as restore targets")
    label = run(["docker", "inspect", "--format", "{{index .Config.Labels \"miccorag.rehearsal\"}}", container]).strip()
    if label != b"true" or not docker_running(container):
        raise GuardError("Staging PostgreSQL container must be running and labelled miccorag.rehearsal=true")


def restore_stage(args: argparse.Namespace) -> Path:
    path = args.backup.resolve(strict=True)
    verify_backup(path)
    stage_guard(args.stage_dir, args.stage_container, args.stage_database)
    # A new stage directory is the only filesystem restore target. No source
    # paths from the manifest are interpreted or used as destinations.
    args.stage_dir.mkdir(mode=0o700, parents=False)
    try:
        with tarfile.open(path / "files.tar.gz") as tar:
            tar.extractall(args.stage_dir, filter="data")
        exists = run(["docker", "exec", args.stage_container, "psql", "-U", DB_USER,
                      "-d", "postgres", "-Atc",
                      f"SELECT 1 FROM pg_database WHERE datname='{args.stage_database}'"])
        if exists.strip():
            raise GuardError("Staging database already exists; refusing overwrite")
        run(["docker", "exec", args.stage_container, "createdb", "-U", DB_USER, args.stage_database])
        with (path / "database.dump").open("rb") as stream:
            run(["docker", "exec", "-i", args.stage_container, "pg_restore", "-U", DB_USER,
                 "-d", args.stage_database, "--no-owner", "--no-acl"], input_file=stream)
        (args.stage_dir / "RESTORE_COMPLETE").write_text(datetime.now(timezone.utc).isoformat() + "\n")
    except BaseException:
        # Keep partial stage evidence for diagnosis. Never touch production.
        raise
    return args.stage_dir


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="action", required=True)
    b = sub.add_parser("backup")
    b.add_argument("--destination", type=Path, required=True)
    for name in ("uploads", "knowledge-graph", "chroma", "config"):
        b.add_argument("--" + name, type=Path, required=True)
    b.add_argument("--backend-port", type=int, action="append", default=[8001])
    b.add_argument("--retention-days", type=int, default=30)
    b.add_argument("--allow-local", action="store_true", help="isolated rehearsal only")
    v = sub.add_parser("verify")
    v.add_argument("--backup", type=Path, required=True)
    s = sub.add_parser("restore-stage")
    s.add_argument("--backup", type=Path, required=True)
    s.add_argument("--stage-dir", type=Path, required=True)
    s.add_argument("--stage-container", required=True)
    s.add_argument("--stage-database", required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        if args.action == "backup":
            print(backup(args))
        elif args.action == "verify":
            verify_backup(args.backup)
            print("Backup checksums and archive paths verified")
        else:
            print(restore_stage(args))
    except (GuardError, OSError, ValueError, tarfile.TarError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
