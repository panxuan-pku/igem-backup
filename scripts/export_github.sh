#!/usr/bin/env bash
# Export the current source view; ignored local files never enter the export.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$ROOT/09_github_export}"
python3 - "$ROOT" "$DEST" <<'PY'
from pathlib import Path
import shutil
import subprocess
import sys

root, dest = (Path(value).resolve() for value in sys.argv[1:])
if dest == root or root.is_relative_to(dest):
    raise SystemExit("Refusing to export over the source tree or its parent")
if dest.exists() and any(dest.iterdir()):
    raise SystemExit(f"Destination is not empty: {dest}")
# --exclude-standard does not remove ignored files that are already tracked.
paths = subprocess.check_output(
    ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
).split(b"\0")
paths = sorted(set(path for path in paths if path))
ignored = subprocess.run(
    ["git", "-C", str(root), "check-ignore", "--no-index", "-z", "--stdin"],
    input=b"\0".join(paths) + b"\0", capture_output=True, check=False,
)
if ignored.returncode not in (0, 1):
    raise SystemExit(ignored.stderr.decode())
skip = set(ignored.stdout.split(b"\0"))
selected = []
for raw in paths:
    if raw in skip:
        continue
    path = root / raw.decode()
    if path.is_relative_to(dest):
        continue
    if path.is_symlink():
        raise SystemExit(f"Export requires regular files, found symlink: {path}")
    if path.is_file():
        selected.append(path)
dest.mkdir(parents=True, exist_ok=True)
for path in selected:
    target = dest / path.relative_to(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
print(f"Source export: {dest} ({len(selected)} files, working-tree content)")
print("This export does not include ignored data, models, or local records; it is not a fresh-clone validation.")
PY
