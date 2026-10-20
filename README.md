I created and maintained vibecoding scaffolding myself


####
1. Anthropic 官方提示词工程指南（2025~2026 最新版）
来源链接：[Claude Prompt Engineering Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) / [Anthropic Resources 2026](https://claude.com/resources/articles/best-practices-for-prompt-engineering)
核心原文：
"Tell Claude what to do instead of what not to do — Instead of: 'Do not use markdown in your response'..."
依据要点：官方在控制输出格式与模型行为时，强调使用正面指令（Positive Instructions）引导模型，而不是密集的负面约束（Negative Constraints）。


2. Anthropic 官方关于模型人格与谄媚（Sycophancy）的研究论文
来源链接：[The Claude’s Character / Considerations in Constructing Claude’s Character](https://www.anthropic.com/research/claude-character)
核心原文与机制：
"If the user corrects Claude or tells Claude it’s made a mistake, then Claude first thinks through the issue carefully before acknowledging the user, since users sometimes make errors themselves."
依据要点：论证了过度防御或过度顺从都会导致模型失真。当面临质疑时，正确的提示词设计是“触发谨慎求证与事实核验”，而不是设计成防御性对抗或者无底线认错。


3. 前沿大模型泄露与公开发布的系统提示词分析（2025 年 5 月）
来源链接：Simon Willison 分析解构的 [Highlights from the Claude 4 system prompt](https://simonwillison.net/2025/May/25/claude-4-system-prompt/) 与 GitHub 社区公开的提示词库 [system-prompts-and-models-of-ai-tools](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools)
核心原文与机制：
针对避免模型欺瞒（Reward Hacking / Sycophancy）的最新设计，官方系统提示词已彻底抛弃早期的粗暴训诫（如“严禁欺骗、严禁犯错”），全面转向“程序化动作定义”——例如要求模型*“遇到不确定项时客观声明边界，在完成严密核验前不给出肯定承诺”*。
####
