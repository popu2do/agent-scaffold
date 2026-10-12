#!/usr/bin/env python3
"""Emit stage checklists and output templates for worktree-task-flow."""

from __future__ import annotations

import argparse


STAGES = {
    "preflight": {
        "title": "前置处理",
        "checks": [
            "读取仓库规则与相关 spec，不先写代码",
            "明确 base_branch / integration_target / remote_scope",
            "检查主工作区是否脏、是否已有同类 worktree、worktree 参数是否一致",
            "确认 integration_target 不被误填为 local-only（该值属于 remote_scope）",
            "记录 baseline commit、非目标和关键风险",
        ],
        "template": [
            "前置完成",
            "- base_branch:",
            "- integration_target:",
            "- remote_scope:",
            "- worktree:",
            "- baseline_commit:",
            "- 风险:",
        ],
    },
    "analysis": {
        "title": "需求分析",
        "checks": [
            "先看文档、spec、测试、日志、截图、样例数据",
            "说明目标、非目标、当前行为、期望行为、证据和风险",
            "bug 或评审任务先复现或审证据，不直接实现",
        ],
        "template": [
            "需求分析",
            "- 目标:",
            "- 非目标:",
            "- 当前行为:",
            "- 期望行为:",
            "- 风险:",
            "- 待确认:",
        ],
    },
    "design": {
        "title": "方案设计",
        "checks": [
            "优先根因修复，不做补丁堆叠",
            "说明影响面、备选方案、测试策略和风险控制",
            "任务大时先拆阶段，再实施",
        ],
        "template": [
            "方案设计",
            "- 核心改法:",
            "- 影响面:",
            "- 不采用的方案:",
            "- 测试策略:",
            "- 风险控制:",
        ],
    },
    "align": {
        "title": "目标对齐",
        "checks": [
            "把当前目标压成短结论，避免以为一致实际跑偏",
            "如果用户要求阶段门禁，在这里等待确认",
            "如果需求已变，回到分析或设计阶段",
        ],
        "template": [
            "目标对齐",
            "- 目标:",
            "- 结果:",
            "- 业务影响:",
            "- 已完成:",
            "- 待完成:",
            "- 风险/冲突:",
        ],
    },
    "implement": {
        "title": "实现与验证",
        "checks": [
            "确保修改只发生在 worktree 内",
            "先最小实现，再补测试和文档",
            "先跑最窄测试，再按风险扩大范围",
            "明确哪些通过、哪些失败、哪些未跑",
        ],
        "template": [
            "实现验证",
            "- 改动摘要:",
            "- 测试通过:",
            "- 测试失败:",
            "- 未执行测试:",
            "- 文档更新:",
            "- 残留风险:",
        ],
    },
    "closeout": {
        "title": "清理收口合入",
        "checks": [
            "明确最终合入目标，不混淆 dev 与 origin/dev",
            "合入后回到目标分支复核结果，不只看 worktree",
            "确认结果正确后，再清理分支和 worktree",
        ],
        "template": [
            "清理收口",
            "- 合入目标:",
            "- 合入方式:",
            "- 测试结论:",
            "- 已完成:",
            "- 未完成:",
            "- 残留风险:",
            "- 可清理项:",
        ],
    },
}

ALIASES = {
    "0": "preflight",
    "1": "analysis",
    "2": "design",
    "3": "align",
    "4": "implement",
    "5": "closeout",
    "alignment": "align",
    "implementation": "implement",
    "cleanup": "closeout",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", help="Stage name or index")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stage_key = ALIASES.get(args.stage, args.stage)
    if stage_key not in STAGES:
        raise SystemExit(f"Unknown stage: {args.stage}")

    stage = STAGES[stage_key]
    print(stage["title"])
    print("- 检查项:")
    for item in stage["checks"]:
        print(f"  - {item}")
    print("- 输出模板:")
    for line in stage["template"]:
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
