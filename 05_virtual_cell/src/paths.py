"""Centralized path resolution for VirtualCellTool.
Replaces the old hardcoded absolute paths with root-relative resolution
(from __file__), so the tool works from any location.
All imports should use these constants instead of constructing paths ad-hoc.
"""
import os

# Root = VirtualCellTool/ directory (one level above this src/ file)
VCT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Third-party checkout remains local, outside the published VCT source.
SIG_DIR = os.path.abspath(os.path.expanduser(os.environ.get("SIGNATURE_DIR", os.path.join(os.path.dirname(VCT_ROOT), "05_tools", "SIGnature"))))

# SCimilarity model weights
MODEL_DIR = os.path.join(SIG_DIR, "model_files", "model_files", "scimilarity")

# VirtualCellTool data directory
DATA_DIR = os.path.join(VCT_ROOT, "data")

# GEARS training data directory
GEARS_DATA_DIR = os.path.join(VCT_ROOT, "gears_data")

# GEARS checkpoint directory
GEARS_CKPT_DIR = os.path.join(VCT_ROOT, "gears_ckpt")


def resolve(path: str) -> str:
    """Resolve a path that may be relative to VCT_ROOT or absolute.
    For paths that start with ~/ or $HOME/, expand user dir.
    """
    if path.startswith("~"):
        path = os.path.expanduser(path)
    if os.path.isabs(path):
        return path
    return os.path.join(VCT_ROOT, path)