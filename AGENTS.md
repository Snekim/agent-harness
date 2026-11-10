# Agent Harness repository instructions

This repository keeps reusable agent definitions, skills, runtime profiles, and workflow settings under version control. Codex is the first runtime. Keep project-specific rules in the projects that use the harness, and task-specific requirements in the task itself.

## Language

- Write instructions for agents and tools in English, including `AGENTS.md`, agent prompts, and `SKILL.md` files and references intended for agents.
- Write documentation for people in both English and Russian. Keep English in `README.md` or `<name>.md` and Russian in `README.ru.md` or `<name>.ru.md`. Link the two versions and update them together in the same change.
- Use conventional English identifiers and comments in code and configuration. Keep commands, paths, and config keys identical across translations.

## Repository conventions

- An agent defines who does the work; a skill describes how to do a reusable task; a workflow defines the order of work. Keep skills usable by more than one agent when practical.
- `harness.yaml` describes the intended environment. `harness.lock.yaml` records external dependency revisions. These are repository formats. Keep manifest entries and actual files aligned as draft components are implemented, and document any remaining gaps.
- Keep external plugins as dependencies. Record verified revisions before claiming that an installation is reproducible. Keep credentials, private session data, and machine-specific settings out of Git.
- For installation changes, verify behavior in a temporary destination before using an active Codex configuration. Preserve unrelated user settings.
- Document the difference between working features and planned ones. When changing a config or workflow, update both language versions of the affected documentation.
