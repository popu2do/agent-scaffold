---
name: sidecar-tasks
description: Orchestrate concurrent subagents by task difficulty and type instead of role. Keep the critical path local, and dispatch bounded, independent sidecar tasks in parallel with tiered reasoning effort (low/medium/high/xhigh) or model tiers.
---

# Sidecar Tasks Parallel Dispatch

Route subagents by task type and complexity, not by role. Keep the critical path local, and delegate sidecar work that can run concurrently.

## Quick Start

1. Confirm the user explicitly asked for subagents/delegation/parallel work.
2. Split work into:
- Critical path: blocking tasks required for your immediate next step (keep local).
- Sidecar tasks: bounded, independent tasks that can run in parallel (delegate).
3. Choose the thinking level / reasoning effort per task type using `references/model-routing.md`.
4. Spawn one worker per disjoint write scope.
5. Continue local work while workers run; wait only when blocked.
6. Integrate outputs, verify tests, then close agents.

## Task Routing Workflow

### Step 1: Build the task graph

Classify each task:
- Blocking now: required before any useful local progress.
- Parallelizable: independent and materially advances delivery.
- Non-delegable: tightly coupled design decisions, high ambiguity, or tiny edits.

Delegate only parallelizable tasks.

### Step 2: Select reasoning effort by task type

Read `references/model-routing.md` and apply its decision table.

Workers inherit the active agent's model by default, or use the configured provider route. Task difficulty is controlled by the thinking level / reasoning effort (or model tier):
- Simple tests / docs / formatting -> `low`
- Daily coding / quick bug fixes -> `medium`
- Complex refactors / cross-file logic -> `high`
- Hard research / very difficult algorithm work -> `xhigh`

### Step 3: Define worker ownership

For each delegated task, specify:
- Goal and acceptance criteria
- Exact file/module ownership (disjoint write sets)
- Constraints (do not revert others, adapt to concurrent edits)
- Required validation command

### Step 4: Dispatch in parallel

Use one spawn call per independent task. Keep prompts concrete and bounded.

Dispatcher prompt template:

```text
Task: <single bounded task>
Model: <inherit default | target model>
Thinking level / Reasoning effort: <low | medium | high | xhigh>
Ownership: <files/modules>
Constraints:
- You are not alone in this codebase.
- Do not revert edits from others.
- Keep changes scoped to ownership.
Validation:
- Run: <command>
Output:
- Summary of changes
- File list changed
- Test/lint results
```

### Step 5: Integrate and verify

1. Review returned diffs for scope and regressions.
2. Resolve conflicts by preserving ownership boundaries.
3. Run narrow tests first, then broader checks if needed.
4. Close agents that are no longer needed.

## Escalation Policy

Escalate the thinking level / model tier only when a lower level repeatedly fails with clear evidence:
- 2 failed attempts with different approaches, or
- repeated loop without new signal, or
- correctness-critical task remains unresolved.

Never start with `xhigh` unless the task is genuinely research-grade/algorithmically difficult, the user explicitly requests it, or lower levels have clearly failed.

## Guardrails

- Do not delegate tasks that block your immediate next local step.
- Do not duplicate work across workers.
- Do not spawn for trivial one-file tiny edits.
- Keep prompts artifact-first (pass files/tasks, not your preferred solution).
- Preserve small-context prompts to reduce leakage and bias.
- Workers must not run destructive git/file operations without explicit user confirmation.
- Workers must not exfiltrate credentials or send secrets to third-party endpoints.
- If install/uninstall/config-change commands are needed, stop and ask for explicit confirmation first.

## References

- Model routing and fallback rules: `references/model-routing.md`
- Chinese dispatch templates: `references/prompt-templates-zh.md`
