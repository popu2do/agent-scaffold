<required_reading>
仅评审流程适用于需求不明确、需要多轮讨论的场景。
</required_reading>

<process>
## 仅评审流程

### 适用场景

- 需求模糊，需要澄清
- 技术方案有多种选择，需要讨论
- 涉及架构变更，需要评估影响
- 用户希望先讨论再决定是否实施

### 流程

派发 Agent1（评审员）：

```markdown
**任务**: 评审需求并提出问题和建议

**第一步**: 读取角色配置 `.claude/skills/multi-agent/agent1-reviewer.md`

**输入**: [用户需求描述]

**规范**:
- `Docs/steering/architecture.md`
- `Docs/interactions/README.md`

**输出**:
1. 需求理解（重述需求）
2. 不明确的点（需要用户澄清）
3. 技术方案建议（如有多种选择，列出优劣）
4. 风险评估
5. 下一步建议（继续讨论 or 开始实施）
```

### 迭代模式

评审后根据用户反馈：

- **继续讨论** → 再次派发 Agent1，带上之前的讨论历史
- **开始实施** → 切换到 full-cycle.md，从“阶段 0：冻结目标”开始
- **暂停** → 等待用户提供更多信息
</process>

<success_criteria>
评审流程成功的标志：

- 需求已充分讨论
- 不明确的点已澄清
- 技术方案已选定
- 用户决定下一步行动
</success_criteria>
