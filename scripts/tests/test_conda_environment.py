"""Conda declarations and the legacy Bash shortcut share the same dependencies."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("filename,name,requirements", [
    ("environment.yml", "virtual-screening", "03_pipeline/requirements.txt"),
    ("environment-vct.yml", "virtual-cell", "05_virtual_cell/requirements-web.txt"),
])
def test_conda_uses_existing_requirements(filename, name, requirements):
    config = yaml.safe_load((ROOT / filename).read_text())
    assert config["name"] == name
    assert "prefix" not in config  # never publish a developer's installation path
    assert config["dependencies"] == ["python=3.11", "pip", {"pip": [f"-r {requirements}"]}]
    assert (ROOT / requirements).is_file()
    assert str(config["variables"]["PYTHONUTF8"]) == "1"


@pytest.fixture
def conda_stub(tmp_path):
    # Exercise the Bash wrapper without installing packages or using a real Conda.
    bash = shutil.which("bash")
    if not bash:
        pytest.skip("legacy Bash shortcut requires Bash; Windows uses Conda directly")
    log = tmp_path / "conda.jsonl"
    stub = tmp_path / "conda"
    stub.write_text(f"#!{sys.executable}\n" +
                    "import json,os,sys\n" +
                    "with open(os.environ['CONDA_TEST_LOG'], 'a') as handle:\n" +
                    "    handle.write(json.dumps(sys.argv[1:])+'\\n')\n" +
                    "sys.exit(int(os.environ.get('CONDA_TEST_EXIT', '0')))\n")
    stub.chmod(0o755)
    env = dict(os.environ, PATH=str(tmp_path) + os.pathsep + os.environ.get("PATH", ""),
               CONDA_TEST_LOG=str(log))
    return bash, log, env


@pytest.mark.parametrize("args,extras,vct", [
    ([], [], False), (["--pipeline-only"], [], False),
    (["--with-cnv"], ["cnv"], False), (["--with-dev"], ["dev"], False),
    (["--with-cnv", "--with-dev", "--with-vct"], ["cnv", "dev"], True),
])
def test_shortcut_installs_only_requested_groups(conda_stub, args, extras, vct):
    bash, log, env = conda_stub
    result = subprocess.run([bash, str(ROOT / "scripts/setup_envs.sh"), *args],
                            env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    commands = [json.loads(line) for line in log.read_text().splitlines()]
    expected = [["env", "create", "--file", "environment.yml"]]
    if extras:
        expected.append(["run", "-n", "virtual-screening", "python", "-m", "pip", "install",
                         *[part for name in extras for part in ("-r", f"03_pipeline/requirements-{name}.txt")]])
    expected.append(["run", "-n", "virtual-screening", "python", "scripts/test_pipeline.py",
                     "--suite", "environment", *["--with-" + name for name in extras]])
    if vct:
        expected.extend([["env", "create", "--file", "environment-vct.yml"],
                         ["run", "-n", "virtual-cell", "python", "-m", "pip", "check"]])
    assert commands == expected


def test_failed_create_does_not_modify_existing_environment(conda_stub):
    bash, log, env = conda_stub
    result = subprocess.run([bash, str(ROOT / "scripts/setup_envs.sh"), "--with-vct"],
                            env=dict(env, CONDA_TEST_EXIT="1"), capture_output=True, text=True)
    assert result.returncode == 1
    assert len(log.read_text().splitlines()) == 1
    assert "Ready" not in result.stdout
