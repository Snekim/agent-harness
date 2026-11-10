"""Check the harness sources and, optionally, a Codex installation."""

import argparse
import shutil
import sys

from harness import (
    CLI_ERRORS,
    add_target_options,
    file_plan,
    file_status,
    load_harness,
    plugin_state,
    require,
    select_target,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_target_options(parser, required=False)
    parser.add_argument("--plugins", action="store_true", help="Check optional plugins in --user scope")
    args = parser.parse_args()
    try:
        target = select_target(args)
        require(not args.plugins or (target and target.codex_home), "--plugins requires --user")
        harness = load_harness()
        print(f"ok: {len(harness.agents)} agents, {len(harness.skills)} skills, "
              f"{len(harness.profiles)} profiles, {len(harness.plugins)} optional plugin pins")
        codex = shutil.which("codex")
        print(f"Codex CLI: {codex or 'not on PATH (needed to run Codex)'}")
        failed = False
        if target:
            for path, state in file_status(file_plan(harness, target)).items():
                if state != "ok":
                    print(f"{state}: {path}")
                    failed = True
            if not failed:
                print("ok: installed harness files match the repository")
        if args.plugins:
            for name, pin in harness.plugins.items():
                state = plugin_state(target.codex_home, name, pin)
                print(f"{state}: {name} {pin['revision']}")
                failed |= state != "ok"
        return int(failed)
    except CLI_ERRORS as error:
        print(f"doctor: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
