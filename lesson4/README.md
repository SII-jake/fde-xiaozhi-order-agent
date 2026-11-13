# 第 4 课 P33 · 用 WorkBuddy 优化订单调查助手

练习从 `main` 分支开始。进入项目根目录，运行基线并保留输出的会话日志。

```sh
python3 -m order_agent.app --config config/local.json --order A1024
python3 -m order_agent.app --config config/local.json --order A1025
python3 -m order_agent.app --config config/local.json --order A1026
```

发给 WorkBuddy 的任务：

> 请用同样的 A1024、A1025、A1026 跑优化前后两版，保留 JSONL。选择一项减少调用和一项减少单次用量的改动。逐单给出模型调用次数，再汇总整单输入和输出 Token。A1024 核对预计送达日，A1025 核对未出库，A1026 核对冲突升级。

每次发出模型请求计一次，回退的模型调用单独计入。逐次汇总输入和输出 Token，输入包含缓存命中部分。API 用实际 usage。Mock 用第 2 课同一 Qwen 聊天模板和分词器复算请求，对模型输出（含工具调用）离线分词，并标注为离线估算。

## 参考实现

参考实现位于 `lesson4-optimized` 分支。课堂讲评可另开一个工作目录，保留学员当前修改。

```sh
git worktree add ../fde-xiaozhi-order-agent-reference lesson4-optimized
cd ../fde-xiaozhi-order-agent-reference
```

在参考实现目录运行：

```sh
python3 -m order_agent.app --config config/optimized.json --order A1024
python3 -m order_agent.web --config config/optimized.json --port 8081
python3 -m lesson4.compare
```

- `config/local.json` 默认运行基线，`config/optimized.json` 打开参考优化。两份配置都使用 Mock。
- `order_agent/optimization.py` 中，应用先查订单，并用返回的运单号取初始物流。模型在一次响应里提出独立查询。政策正文保留 ID 和正文，原始工具结果继续写入日志。
- 固定系统指令在前，业务日期随订单上下文发送。准备好证据后，末次请求清空工具并按四项要求答复。A1024 的简单答复用 Flash，复杂情况用 GLM-5.3。Flash 缺关键事实时退回 GLM-5.3。
- `python3 -m lesson4.compare` 对两版使用同一旗舰模型标识作为取证基线。它保留两个流程的调用、请求字符数、末轮工具数和答复对照。输入字符数不是 Token 数。缓存命中、账单和真实模型质量需要在线复测。
- 若有合适的 API，在 `config/` 下复制 `optimized.json`，将新配置的 `llm.backend` 改成 `api`，并通过 `LLM_API_KEY` 提供凭证。再复制一份 API 配置并删除 `agent.optimization` 作为在线基线。两版用同一模型端点和价目。清空工具的请求带历史工具消息，先验证服务端兼容性。

[参考回放结果](../lessons/lesson-04/materials/lesson4-demo-comparison.json) · [业务验收用例](../lessons/lesson-04/materials/acceptance-cases.json)

## 复算 P32 的模型调用次数和 Token 数

在项目根目录的 Python 环境安装 `tokenizers` 和 `jinja2`，再运行 `python3 -m lesson4.measure_span_tokens`。输出中的 model_calls 是模型调用次数，并提供同一 Qwen 分词口径下的整单输入和输出 Token。 [三笔订单参考结果](../lessons/lesson-04/materials/lesson4-span-token-comparison.json)
