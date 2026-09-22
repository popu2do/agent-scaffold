---
name: multi-agent
description: 任务可拆分为 2 个及以上低耦合子问题时使用，通过主控统一目标、并行探索和独立验证，避免角色流水线造成的信息衰减与目标漂移。
---

# 多路 Agent 协作工作流（Orchestrator-Worker）

你是总指挥（Orchestrator）。你持有唯一全局目标，负责拆分、汇总、裁决与对外沟通。

## 何时使用

适用：
- 任务可分为多个相互独立子问题
- 需要并行检索、并行实现或并行验证
- 需要在长链路任务中保持目标一致性

不适用：
- 单点小改动（一个 Agent 可完成）
- 强顺序依赖且无法拆分的任务

## 核心责任模型

1. **主控责任（唯一）**：总指挥持有完整目标与约束，只由总指挥做最终裁决。
2. **并行责任（多个）**：Worker 仅处理独立子问题，返回证据与候选结论。
3. **验证责任（独立）**：验证 Agent 只找错、找漏、找反例，不直接接手实现。

## 强制机制

### 1) 先冻结目标
先产出任务目标快照（目标、非目标、约束、验收条件），再派发。

### 2) 轻量状态记录
总指挥每轮保留一行状态记录（可写在回复或任务日志中），无需强制单独文件。
推荐格式：`[目标变化?][本轮完成][判断依据][风险/下一步]`。

### 3) 不做岗位接力
禁止固定 PM→架构→开发→测试 的线性接力作为默认路径。
优先：主控拆分 → Worker 并行 → 独立验证 → 主控综合。

## 最小执行流程

1. 总指挥冻结目标与验收条件。
2. 按“可独立完成”原则拆分子任务。
3. 并行派发 Worker（可复用 Agent3/Agent4 等角色）。
4. 汇总候选结果与证据。
5. 独立派发验证 Agent（优先 Agent2 或 Agent1）输出：错误点/漏项/反例。
6. 总指挥裁决并给用户最终方案。

详见 [workflows/full-cycle.md](workflows/full-cycle.md)。

## 派发模板

```markdown
**任务**: [子任务描述]

**第一步**: 读取角色配置 `.claude/skills/multi-agent/agent[N]-[role].md`

**约束**:
- 不持有全局裁决权
- 输出必须包含证据（文件/行号、命令、测试结果）
- 不得越权修改子任务边界之外内容

**输入**: [目标快照 + 当前状态片段 + 子任务输入]

**输出**: [候选结论 + 证据 + 风险]
```

## 角色映射（可复用）

- Agent1：评审/汇报（可做独立验证）
- Agent2：质量门禁/验收（推荐独立验证）
- Agent3：实现者（并行实现）
- Agent4：文档员（并行文档）

## 业务与技术边界

- 业务问题（交互、默认行为、流程定义）必须上报用户。
- 技术问题（不改变外部行为的内部实现）由 Agent 自治。

## 参考

- 完整流程: [workflows/full-cycle.md](workflows/full-cycle.md)
- 快速通道: [workflows/fast-track.md](workflows/fast-track.md)
- 仅评审: [workflows/review-only.md](workflows/review-only.md)
- 优化技巧: [workflows/optimization.md](workflows/optimization.md)
- 决策模板: [references/decision-template.md](references/decision-template.md)
- 验收模板: [references/acceptance-template.md](references/acceptance-template.md)
- 测试模式: [references/test-patterns.md](references/test-patterns.md)
- 代码标准: [references/code-standards.md](references/code-standards.md)
- 检查清单: [references/checklist.md](references/checklist.md)
