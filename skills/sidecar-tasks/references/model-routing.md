# Model & Effort Routing

## Decision Table

Choose task difficulty and compute budget through the thinking level (reasoning effort) or model tiers, rather than arbitrary model switching. Subagents inherit the parent agent's model route by default.

1. Simple tests / docs / formatting
- Reasoning effort / Tier: `low` (or fast model)
- Typical tasks: add unit tests, improve comments, style/lint cleanup

2. Daily coding / quick bug fix
- Reasoning effort / Tier: `medium` (standard model)
- Typical tasks: fix one bug, adjust business logic, small feature patch

3. Complex refactor / cross-file logic
- Reasoning effort / Tier: `high` (strong model)
- Typical tasks: architecture refactor, dependency untangling, multi-module behavior change

4. Hard research / very difficult algorithms
- Reasoning effort / Tier: `xhigh` (deep reasoning model)
- Trigger: genuinely difficult work, or escalation after lower levels fail repeatedly

## Escalation and Fallback

- Start at the lowest tier that matches task complexity.
- Escalate one level at a time.
- Record why escalation happened (failure signal, not preference).
- De-escalate for follow-up cleanup tasks when their actual complexity is lower.

## Parallel Dispatch Heuristics

- Prefer parallelism when tasks are independent and write scopes do not overlap.
- Keep critical-path tasks local in the main agent.
- Do not wait by reflex; only wait when blocked by worker result.

## Example Routing

- "修复登录接口偶发 500" -> tier: `medium`
- "重构支付模块并拆分服务边界" -> tier: `high`
- "补齐测试并更新注释" -> tier: `low`
- "多次失败的组合优化算法" -> tier: `xhigh`
