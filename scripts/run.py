"""Run a task in an installed project using the harness roles and developer profile."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from harness import CLI_ERRORS, file_plan, file_status, load_harness, project_target, read_toml, require


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--prompt-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        harness = load_harness()
        target = project_target(args.project)
        mismatches = [str(path) for path, state in file_status(file_plan(harness, target)).items()
                      if state != "ok"]
        require(not mismatches, "Run install.py or doctor.py for this project. Files do not match: "
                + ", ".join(mismatches))
        prompt = args.prompt_file.read_text(encoding="utf-8")
        require(prompt.strip(), "The prompt file is empty")
        profile_path = next(path for path in harness.profiles if path.name == "developer.config.toml")
        profile = read_toml(profile_path)
        threads = profile["agents"]["max_concurrent_threads_per_session"]
        command = ["codex", "-a", "never", "exec", "--ignore-user-config", "--skip-git-repo-check",
                   "--sandbox", "workspace-write", "-C", str(target.agents.parents[1]),
                   "-m", profile["model"], "-c", f"model_reasoning_effort={profile['model_reasoning_effort']}",
                   "-c", f"agents.max_concurrent_threads_per_session={threads}"]
        for agent in harness.agents:
            config_file = json.dumps(str(target.agents / agent.name), ensure_ascii=False)
            command.extend(["-c", f"agents.{agent.stem}.config_file={config_file}"])
        return subprocess.run([*command, "-"], input=prompt, text=True, check=False).returncode
    except CLI_ERRORS as error:
        print(f"run: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
