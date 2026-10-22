"""Run a local probe on the read-only remote checkout via SSH stdin."""
from pathlib import Path
import os
import subprocess
import sys

base = Path(__file__).resolve().parent
name = sys.argv[1]
assert name in {"live", "isolated", "sqlite"}
source = base / f"business_{name}_probe.py"
output = base / f"business-{name}-raw.json"
lines = Path("/root/MiccoRAG/vps_ssh_info.txt").read_text().splitlines()
host = lines[1].split(":", 1)[1].strip()
user, password = lines[2].split("/", 1)
command = ["sshpass", "-e", "ssh", "-o", "ConnectTimeout=15", f"{user}@{host}",
           "cd /home/micco/MiccoRAG-v3/micco-backend/backend && PYTHONPATH=/tmp/micco-eval-20260929-py:. ../venv/bin/python -"]
result = subprocess.run(command, input=source.read_bytes(), capture_output=True,
                        env={**os.environ, "SSHPASS": password}, timeout=90)
output.write_bytes(result.stdout)
(base / f"business-{name}-stderr.log").write_bytes(result.stderr)
print(f"{name}: exit={result.returncode} stdout_bytes={len(result.stdout)}")
if result.stderr:
    print(result.stderr.decode(errors="replace")[-2000:], file=sys.stderr)
sys.exit(result.returncode)
