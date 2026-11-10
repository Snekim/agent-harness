---
name: harness-workflow
description: Run the Agent Harness plan, implementation, verification, and review workflow using the architect, backend, frontend, and reviewer roles in Codex. Use when asked to run the harness or coordinate a task through these stages.
---

# Harness workflow

1. Read the target repository's instructions. Restate the acceptance criteria, then ask the `architect` for a short plan if the change crosses boundaries. Use `$task-decomposition` for ownership and dependencies. For a smoke test, use all named roles requested by the user even if the task is small.
2. Give `backend` and `frontend` their respective file ownership, contract, relevant standard, and checks. Ask each worker to read its standard skill before editing. Run them in parallel only after the interface is agreed and file ownership is disjoint. Assign a single-layer task to just the relevant implementer.
3. Inspect the combined changes, including untracked files, and run relevant tests. If a check cannot run, explain what remains unverified. Ask `reviewer` to inspect the actual result against the acceptance criteria and report findings before delivery. Address valid findings and rerun the affected checks.
4. Report what changed, which roles actually ran, and what was verified. If a role cannot start, report the failure and whether work continued inline; do not present inline work as delegation. Leave commit, push, and merge to an explicit user request.

This workflow is a local alternative to Compound Engineering. Use Compound Engineering separately when the user requests it.
