"""Read the repository manifest and plan safe, additive Codex installs."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
ROLE_MODELS = {
    "architect": "architect",
    "backend": "developer",
    "frontend": "developer",
    "reviewer": "reviewer",
}


class HarnessError(Exception):
    pass


def require(condition: object, message: str) -> None:
    if not condition:
        raise HarnessError(message)


def read_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path}: expected a YAML mapping")
    return value


def read_toml(path: Path) -> dict:
    with path.open("rb") as file:
        return tomllib.load(file)


def names(values: object, label: str) -> list[str]:
    require(isinstance(values, list) and all(isinstance(value, str)
            and len(value) <= 64 and NAME.fullmatch(value) for value in values),
            f"{label}: expected a list of lowercase, hyphenated names")
    require(len(values) == len(set(values)), f"{label}: duplicate name")
    return values


@dataclass(frozen=True)
class Harness:
    agents: tuple[Path, ...]
    skills: tuple[Path, ...]
    profiles: tuple[Path, ...]
    plugins: dict[str, dict]


def load_harness(root: Path = ROOT) -> Harness:
    manifest = read_yaml(root / "harness.yaml")
    lock = read_yaml(root / "harness.lock.yaml")["dependencies"]
    require(manifest["runtime"] == {"primary": "codex", "orchestration": "native"},
            "Only native Codex orchestration is supported")
    roles = names(manifest["agents"], "agents")
    require(set(roles) == set(ROLE_MODELS), "Expected architect, backend, frontend, and reviewer")
    skills = names(manifest["skills"]["global"], "skills.global")
    workflow = manifest["workflow"]
    limit = workflow["max_parallel_agents"]
    require(type(limit) is int and limit > 0, "max_parallel_agents must be a positive integer")
    require(workflow["default"] == "harness-workflow" and "harness-workflow" in skills
            and workflow["require_review"] is True and workflow["require_tests"] is True
            and workflow["auto_merge"] is False,
            "The MVP workflow is harness-workflow with tests, review, and no automatic merge")

    agents = tuple(root / "agents" / f"{role}.toml" for role in roles)
    skill_files = tuple(root / "skills" / skill / "SKILL.md" for skill in skills)
    profiles = tuple(root / "profiles" / "codex" / f"{role}.config.toml"
                     for role in ("architect", "developer"))
    missing = [str(path.relative_to(root)) for path in (*agents, *skill_files, *profiles)
               if not path.is_file()]
    require(not missing, "Missing manifest files: " + ", ".join(missing))

    def check_model(data: dict, model_role: str, path: Path) -> None:
        expected = manifest["models"][model_role]
        for key, config_key in (("model", "model"), ("effort", "model_reasoning_effort")):
            value = expected[key]
            require(isinstance(value, str) and value.strip() and data.get(config_key) == value,
                    f"{path}: {config_key} must match a nonblank models.{model_role}.{key}")

    for path in agents:
        data = read_toml(path)
        require(data.get("name") == path.stem and all(isinstance(data.get(key), str)
                and data[key].strip() for key in ("description", "developer_instructions")),
                f"{path}: expected matching name, description, and developer_instructions")
        check_model(data, ROLE_MODELS[path.stem], path)

    for path in profiles:
        data = read_toml(path)
        check_model(data, path.name.split(".")[0], path)
        actual = data.get("agents", {}).get("max_concurrent_threads_per_session")
        require(type(actual) is int and actual == limit,
                f"{path}: agent concurrency differs from the manifest")

    for path in skill_files:
        lines = path.read_text(encoding="utf-8").splitlines()
        require(lines and lines[0] == "---" and "---" in lines[1:], f"{path}: missing frontmatter")
        end = lines.index("---", 1)
        data = yaml.safe_load("\n".join(lines[1:end]))
        require(isinstance(data, dict) and data.get("name") == path.parent.name
                and isinstance(data.get("description"), str) and data["description"].strip()
                and any(line.strip() for line in lines[end + 1:]),
                f"{path}: expected matching name, description, and instructions")

    plugin_entries = manifest["plugins"]
    plugin_names = names([plugin["name"] for plugin in plugin_entries], "plugins")
    require(set(plugin_names) == set(lock), "Plugin names differ between manifest and lock")
    plugins = {}
    for plugin in plugin_entries:
        name = plugin["name"]
        pin = lock[name]
        require(pin["repository"] == plugin["source"]
                and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", pin["repository"])
                and re.fullmatch(r"[0-9a-f]{40}", pin["revision"])
                and re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?", pin["version"])
                and pin["installation"] == "codex-plugin", f"{name}: invalid plugin lock")
        names([pin["marketplace"]], f"{name} marketplace")
        require(type(plugin["enabled"]) is bool, f"{name}: enabled must be a boolean")
        if plugin["enabled"]:
            plugins[name] = pin
    return Harness(agents, tuple(path.parent for path in skill_files), profiles, plugins)


@dataclass(frozen=True)
class Target:
    agents: Path
    skills: Path
    codex_home: Path | None = None


def add_target_options(parser: argparse.ArgumentParser, *, required: bool) -> None:
    scope = parser.add_mutually_exclusive_group(required=required)
    scope.add_argument("--project", type=Path, help="Install into this existing project directory")
    scope.add_argument("--user", action="store_true", help="Use Codex user directories")
    parser.add_argument("--codex-home", type=Path, help="Override Codex home for --user")
    parser.add_argument("--skills-dir", type=Path, help="Override the user skills directory for --user")


def select_target(args: argparse.Namespace) -> Target | None:
    require(not (args.codex_home or args.skills_dir) or args.user,
            "--codex-home and --skills-dir require --user")
    if args.project is not None:
        return project_target(args.project)
    if args.user:
        require(bool(args.codex_home) == bool(args.skills_dir),
                "Pass both --codex-home and --skills-dir when staging a user install")
        user_home = Path.home().resolve()
        home = destination_root(args.codex_home or Path(os.environ.get("CODEX_HOME") or user_home / ".codex"))
        skills = destination_root(args.skills_dir) if args.skills_dir else user_home / ".agents" / "skills"
        return Target(home / "agents", skills, home)
    return None


def project_target(project: Path) -> Target:
    project = project.expanduser()
    require(project.is_dir() and not project.is_symlink(), f"Not a project directory: {project}")
    project = project.resolve()
    return Target(project / ".codex" / "agents", project / ".agents" / "skills")


def destination_root(path: Path) -> Path:
    path = path.expanduser().absolute()
    # Normalize aliases such as macOS /tmp while preserving a symlink at the selected root.
    return path.parent.resolve() / path.name


def file_plan(harness: Harness, target: Target) -> dict[Path, Path]:
    files = {target.agents / path.name: path for path in harness.agents}
    for skill in harness.skills:
        require(not skill.is_symlink(), f"Skill directory cannot be a symlink: {skill}")
        for path in sorted(skill.rglob("*")):
            require(not path.is_symlink(), f"Skill files cannot be symlinks: {path}")
            relative = path.relative_to(skill)
            if not path.is_file() or any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
                continue
            files[target.skills / skill.name / relative] = path
    if target.codex_home is not None:
        files.update({target.codex_home / path.name: path for path in harness.profiles})
    return files


def file_status(files: dict[Path, Path]) -> dict[Path, str]:
    result = {}
    for dest, source in files.items():
        if destination_conflict(dest):
            result[dest] = "conflict"
        elif not dest.exists():
            result[dest] = "missing"
        else:
            result[dest] = "ok" if dest.read_bytes() == source.read_bytes() else "conflict"
    return result


def destination_conflict(path: Path, *, directory: bool = False) -> bool:
    if any(parent.is_symlink() or (parent.exists() and not parent.is_dir()) for parent in path.parents):
        return True
    expected_kind = path.is_dir if directory else path.is_file
    return path.is_symlink() or (path.exists() and not expected_kind())


def write_new_files(files: dict[Path, Path], status: dict[Path, str]) -> None:
    require("conflict" not in status.values(), "Resolve conflicting paths before installing")
    for dest, source in files.items():
        if status[dest] == "missing":
            dest.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as src, dest.open("xb") as out:
                shutil.copyfileobj(src, out)


def plugin_state(home: Path, name: str, pin: dict) -> str:
    market = pin["marketplace"]
    config_path = home / "config.toml"
    checkout = home / "plugins" / "cache" / market / name / pin["version"]
    marketplace_checkout = home / ".tmp" / "marketplaces" / market
    if (destination_conflict(config_path) or destination_conflict(checkout, directory=True)
            or destination_conflict(marketplace_checkout, directory=True)):
        return "conflict"
    config = read_toml(config_path) if config_path.is_file() else {}
    marketplace = config.get("marketplaces", {}).get(market)
    expected = {"source_type": "git", "source": plugin_source(pin), "ref": pin["revision"]}
    if marketplace is not None and any(marketplace.get(key) != value for key, value in expected.items()):
        return "conflict"
    if marketplace is None:
        return "conflict" if checkout.exists() else "add marketplace and plugin"
    if checkout.exists():
        if not matches_plugin_pin(checkout, pin["revision"]):
            return "conflict"
        if config.get("plugins", {}).get(f"{name}@{market}", {}).get("enabled") is True:
            return "ok"
    return "add plugin"


def matches_plugin_pin(checkout: Path, revision: str) -> bool:
    git_dir = checkout / ".git"
    if not git_dir.is_dir() or git_dir.is_symlink():
        return False
    git = ["git", "-C", str(checkout)]
    head = subprocess.run([*git, "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    if head.returncode or head.stdout.strip() != revision:
        return False
    diff = subprocess.run([*git, "diff", "--raw", "--no-ext-diff", "--no-renames", "HEAD", "--"],
                          capture_output=True, text=True, check=False)
    # Codex omits tracked symlinks when copying the marketplace checkout to its plugin cache.
    return diff.returncode == 0 and all(
        line.startswith(":120000 000000 ") and line.partition("\t")[0].endswith(" D")
        for line in diff.stdout.splitlines()
    )


def plugin_source(pin: dict) -> str:
    return f"https://github.com/{pin['repository']}.git"


def install_plugin(home: Path, name: str, pin: dict, state: str) -> None:
    if state == "ok":
        return
    require(state != "conflict", f"{name}: existing marketplace or cache differs from the lock")
    home.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "CODEX_HOME": str(home)}
    commands = []
    if state == "add marketplace and plugin":
        commands.append(["marketplace", "add", plugin_source(pin), "--ref", pin["revision"]])
    commands.append(["add", f"{name}@{pin['marketplace']}"])
    for command in commands:
        subprocess.run(["codex", "plugin", *command], env=env, check=True)
    require(plugin_state(home, name, pin) == "ok", f"{name}: Codex did not install the locked revision")


CLI_ERRORS = (HarnessError, OSError, KeyError, TypeError, ValueError, yaml.YAMLError,
              subprocess.CalledProcessError)
