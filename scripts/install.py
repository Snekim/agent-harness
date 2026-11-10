"""Install local harness files. An explicit scope is required."""

import argparse
import shutil
import sys

from harness import (
    CLI_ERRORS,
    add_target_options,
    file_plan,
    file_status,
    install_plugin,
    load_harness,
    plugin_state,
    require,
    select_target,
    write_new_files,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_target_options(parser, required=True)
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--with-plugins", action="store_true", help="Install locked plugins in --user scope")
    args = parser.parse_args()
    try:
        target = select_target(args)
        require(not args.with_plugins or target.codex_home, "--with-plugins requires --user")
        harness = load_harness()
        files = file_plan(harness, target)
        status = file_status(files)
        plugins = {}
        if args.with_plugins:
            plugins = {name: plugin_state(target.codex_home, name, pin)
                       for name, pin in harness.plugins.items()}
        for path, state in status.items():
            print(f"{'add' if state == 'missing' else state}: {path}")
        for name, state in plugins.items():
            print(f"{state}: {name} {harness.plugins[name]['revision']}")
        if args.dry_run:
            return int("conflict" in status.values() or "conflict" in plugins.values())
        require("conflict" not in plugins.values(), "Resolve marketplace or plugin conflicts before installing")
        if any(state != "ok" for state in plugins.values()):
            require(shutil.which("codex") and shutil.which("git"), "codex and git must be on PATH")
        write_new_files(files, status)
        for name, state in plugins.items():
            install_plugin(target.codex_home, name, harness.plugins[name], state)
        print("Harness files are installed.")
        return 0
    except CLI_ERRORS as error:
        print(f"install: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
