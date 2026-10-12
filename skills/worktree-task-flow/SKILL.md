---
name: worktree-task-flow
description: "Use when the user wants isolated parallel work in a git worktree and expects a staged delivery flow: preflight, requirement analysis, solution design, goal alignment, implementation with tests/docs, merge, and cleanup. Trigger on 开个worktree, 隔离开发, 专项重构, 需求探索, 需求分析, 方案设计, 对齐目标, 合入, 收口, or 清理worktree."
---

# Worktree Task Flow

在需要实际创建或复用 worktree 时，先明确声明：`我将使用 $worktree-task-flow，在隔离 worktree 中推进这项任务。`

把 worktree 当成一个完整任务容器来用，而不是只把它当成一个 Git 子目录。

worktree 根目录默认命名为 `<project>-worktrees`，可通过 `--worktree-root` 覆盖。

核心阶段固定为：

1. 前置处理
2. 需求分析
3. 方案设计
4. 目标对齐
5. 实现 + 测试 + 文档
6. 清理收口合入

如果仓库已有更严格的仓库级规则，例如 `AGENTS.md`、`CLAUDE.md`、文档驱动规范、分层架构规则，始终优先遵守仓库规则。

## 使用脚本

把稳定、重复、可执行的部分交给 `scripts/`。

这里的相对路径例如 `scripts/...`、`references/...`，默认都是**相对当前 skill 目录**解析，不是相对目标仓库根目录解析。

目标仓库里没有这些脚本是正常情况；只要 skill 目录下存在对应文件，就应直接使用 skill 自带脚本，不要误判为“仓库缺脚本”后改成人工替代。

### 1. 前置检查

创建或复用 worktree 前，先运行：

```powershell
python "scripts/worktree_preflight.py" --repo "." --base-branch "<base_branch>" --integration-target "<integration_target>" --remote-scope "<remote_scope>" --task-slug "<task_slug>"
```

参数必须按当前仓库真实上下文填写，禁止直接沿用示例值。至少在执行前确认：
- `base_branch`：本次专项的真实起点分支（例如 `dev`、`main`、`release/*`）。
- `integration_target`：本次专项计划最终落地的真实目标分支；若尚未确定，显式标记为 `<unset>`，不要用权限标识占位。
- `remote_scope`：远程触达范围；若尚未明确，显式标记为 `local-only`，不要默认触碰 `origin/*`。
- `task_slug`：与任务一一对应，避免复用旧任务标识。

这个脚本负责输出稳定的前置摘要，固定检查这些点：

- 当前分支与 baseline commit
- 主工作区是否有未提交修改
- worktree_root 与 suggested_worktree 是否符合本次任务参数
- 当前已有的 worktree
- `base_branch / integration_target / remote_scope` 是否存在明显冲突

### 2. 阶段门禁

进入新阶段前，先运行：

```powershell
python "scripts/stage_gate.py" preflight
python "scripts/stage_gate.py" analysis
python "scripts/stage_gate.py" design
python "scripts/stage_gate.py" align
python "scripts/stage_gate.py" implement
python "scripts/stage_gate.py" closeout
```

这个脚本负责输出：

- 当前阶段检查项
- 当前阶段汇报模板

如果用户要求“每个阶段都确认”，在阶段输出后停下等待确认。

## 核心规则

- 先读规则和 spec，再动代码。
- 明确区分 `base_branch`、`integration_target`、`remote_scope`。
- 不允许硬编码或默认假设集成目标分支；任何分支参数都必须来源于当前任务上下文。
- 全流程使用同一个 `worktree_root` 和 `task_slug` 约定，避免任务混线。
- 只在 worktree 内实施修改；改到主工作区时立即纠正。
- 需求变更、证据翻转、测试否定方案时，回到上一阶段，不硬推。
- 除非有明确硬需求，否则不要引入兼容、回退、防呆、双轨逻辑。
- 未经用户明确确认，不执行 `git commit`、`git push`、`merge`、`rebase`、`cherry-pick`、删除 worktree 或删除分支。

## 按需补读

任务复杂时再读，不要默认整份加载：

- 前置、分析、设计、对齐、实现阶段细则：`references/stage-details.md`
- 合入、复核、清理顺序：`references/merge-closeout.md`

## 不适用场景

- 只是回答一个简单问题，不需要隔离工作区
- 不涉及代码或文档变更
- 用户明确要求不要开 worktree
