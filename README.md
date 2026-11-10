# agent-harness

[Русская версия](README.ru.md)

`agent-harness` keeps reusable Codex roles, skills, and model profiles in Git. The MVP runs on native Codex orchestration. Compound Engineering is available as an optional, pinned plugin. Herdr is outside the MVP.

| Component | What it does |
| --- | --- |
| [`harness.yaml`](harness.yaml) and [`harness.lock.yaml`](harness.lock.yaml) | Describe the setup and pin Compound Engineering to a Git revision. These are formats used by this repository. |
| [`agents/`](agents/) | `architect` plans on `gpt-6-astra`; `backend`, `frontend`, and `reviewer` use `gpt-6.1-sol`. |
| [`skills/`](skills/) | `$architecture-review`, `$api-design`, `$task-decomposition`, `$backend-standard`, `$frontend-standard`, and `$harness-workflow`. |
| [`profiles/codex/`](profiles/codex/) | `architect` and `developer` CLI profiles. Each limits concurrent agent threads to four. |
| [`scripts/doctor.py`](scripts/doctor.py) and [`scripts/install.py`](scripts/install.py) | Validate the sources and install or check the declared files. |

## Install and run

Use `uv` with Python 3.11 or later and a recent Codex CLI. For model runs, sign in with `codex login` and check access to the models in the manifest. See the official [skills](https://developers.openai.com/codex/skills), [subagents](https://developers.openai.com/codex/subagents), and [profiles](https://developers.openai.com/codex/config-advanced#profiles) documentation for how Codex discovers these files.

From this repository, validate and install into a project:

```bash
uv run --locked python scripts/doctor.py
uv run --locked python scripts/install.py --project /path/to/project --dry-run
uv run --locked python scripts/install.py --project /path/to/project
uv run --locked python scripts/doctor.py --project /path/to/project
codex -C /path/to/project
```

Project install copies roles to `.codex/agents/` and skills to `.agents/skills/`. Trust the project in Codex to use project roles interactively. In a new session, prompt with `Use $harness-workflow for this task: …` and give it the expected behavior and checks. The workflow does not commit, push, or merge.

For a personal install across projects, use `--user` instead of `--project`. It also installs profiles into `CODEX_HOME` (default `~/.codex`) and puts skills under `~/.agents/skills/`. Start with `codex --profile architect` or `codex --profile developer`. To stage a personal install elsewhere, pass both `--codex-home` and `--skills-dir` along with `--user`.

Repeated installs skip identical files. If an existing file differs, the installer stops before copying anything. Compare the reported files and decide which version to keep before retrying.

## Optional: Compound Engineering

```bash
uv run --locked python scripts/install.py --user --with-plugins --dry-run
uv run --locked python scripts/install.py --user --with-plugins
uv run --locked python scripts/doctor.py --user --plugins
```

The opt-in step uses Codex's plugin commands to install the locked Git revision. It updates the Codex plugin configuration; a marketplace already configured with a different source or ref is reported as a conflict. The plugin check verifies the cached Git revision and detects edits to tracked files. If a download fails, rerun after restoring network access. The local workflow works without the plugin.

## Try the smoke task

From the repository root, copy the starter into a temporary directory. Node.js is needed for the frontend checks.

```bash
demo="$(mktemp -d)"
cp -R examples/smoke/. "$demo/"
uv run --locked python scripts/install.py --project "$demo"
uv run --locked python scripts/doctor.py --project "$demo"
uv run --locked python scripts/run.py --project "$demo" --prompt-file "$demo/task.txt"
(cd "$demo" && python3 check_status.py && node --test check_status.test.mjs)
```

[`run.py`](scripts/run.py) starts Codex with the installed roles and the developer model profile. It passes the roles explicitly, so the demo can run without loading personal config or adding the demo folder to the trust list. It uses the current Codex login.

The [task](examples/smoke/task.txt) exercises all four roles. The backend adds `message: "Service is healthy"` to the existing status response; the frontend displays it and keeps the fallback on request failure. The checks intentionally fail on the starter until the feature is implemented. To see the result in a browser, run `python3 server.py` in the demo directory and visit `http://127.0.0.1:8000`.

Run the harness's own tests without starting Codex: `uv run --locked python -m unittest discover -s tests -v`.

See [AGENTS.md](AGENTS.md) for repository conventions. Agent instructions are in English; documentation for people is maintained in English and Russian.
