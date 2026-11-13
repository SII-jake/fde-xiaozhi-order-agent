# 第 4 课练习与参考答案

## P04｜计算 A1024 的 API 费用

沿用[练习 1 的会话 JSON](../../lesson-01/materials/session-history.json) 中的 `teaching_usage.calls` 和课件费率。请 WorkBuddy 按同一任务逐笔算账，再比较全部输入命中和全部未命中。参考[演算与逐笔答案](api-cost-exercise.md)和[可运行的成本计算代码](../scripts/calculate_api_cost.py)。

## P33｜用 WorkBuddy 优化订单调查助手

从[优化前的 Demo](../../../lesson4/README.md)开始，按课堂方法修改。用相同订单复跑，报告模型调用次数、输入 Token 数和输出 Token 数。讲评时可对照[参考实现结果](lesson4-span-token-comparison.json)。

## 课堂演示素材

每页可复制的 WorkBuddy 提示词在[讲稿](../lesson-04-script.md)。先保存基线与候选，再用[验收用例](acceptance-cases.json)核对业务行为。

| 页 | 输入与起点 | 参考答案或验收 |
|---|---|---|
| P10 一次响应提出两项工具调用 | [原始会话](../../lesson-01/materials/session-history.jsonl)、[双工具响应](multi-tool-message.json)、[回放脚本](../scripts/replay_multi_tool.py) | Mock 回放模型调用 7 → 6，工具执行仍为 6。下一请求携带两条不同调用 ID 的工具消息。 |
| P13 预取订单 | 原始会话、第 1 次请求和订单工具 | 第 1 次模型请求已有 A1024、运单 TA1024 和承诺日期。无订单号时继续澄清，取数失败时保留原错误出口。实际调用次数待测。 |
| P16 封装订单和物流 | 原始会话、订单与物流工具、[工具依赖图](tool-dependencies.mmd) | 调用 get_order_tracking(A1024) 时，内部先查订单再用 TA1024 查物流，末尾复查仍保留。候选尚需集成验证。 |
| P19 过滤政策前置页 | [实验步骤](application-experiments.md)、[政策输入](policy-document-front-matter.json)、[字段对照](policy-projection-example.json) | 第 5、6 次输入各少 205，整笔 10,040 → 9,630，保留编号与政策原文。 |
| P22 限定答复格式 | 过滤政策后的 A1024 末次请求、A1026 冲突验收条件 | 答复应覆盖延误和证据、预计日期且不保证、联系承运商、超过三天进入审核。输出 token 需要用真实模型对照。 |
| P25 稳定前缀 | [完整 Prompt](prefix-prompt-example.json) | 对比时间放在 System 开头与 User 末尾时的公共前缀。 |
| P28 模型路由 | [A1024、A1026 订单样本](../../../data/orders.json)与[讲稿提示词](../lesson-04-script.md) | 简单物流答复走 GLM-5.3-Flash，冲突证据走 GLM-5.3。Flash 答复漏关键事实时回退，计入两次费用。 |
| P31 动态工具数量 | [请求导出脚本](../scripts/prepare_request_examples.py)中的 method_8 | 两版只改 tools。核对答复的延误原因、预计送达日和建议，再按实际 usage 比较费用。离线输入 1,834 → 603。 |

[参考核对代码](../scripts/check_optimization_examples.py)可直接运行，检查双工具样例、政策字段与 token 差异、模拟工单路由和缓存计费算例。需要运行目标模型的步骤以实际 API 输出为准。

## 可直接交给 WorkBuddy 的回放文件

- [原流程七次调用](a1024-single-tool.jsonl)和[合并后六次调用](a1024-multi-tool.jsonl)使用同一份政策输入，适合 P10 对照。P13、P16 可以从七次调用版单独开始。
- [六次调用＋已过滤前置页](a1024-filtered.jsonl)与[参考改动补丁](filter-policy-front-matter.patch)用于 P19 核对。补丁作用于基线练习副本。三份记录的工具结果都保留完整政策。
- P22、P31 的具体模型请求可用[请求样例提取代码](../scripts/prepare_request_examples.py)导出。分别生成答复指令对照和末次保留或清空工具的请求。比较 token 时使用同一 Qwen 聊天模板与分词器。
