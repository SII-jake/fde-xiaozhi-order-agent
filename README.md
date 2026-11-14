# 小智的订单调查助手

独立的学员Git项目，Python 3.10+，运行不需要第三方依赖。业务工具全部mock，无真实退款、消息或工单提交。

## 课堂练习

| 练习 | 要求 | 发放材料 |
|---|---|---|
| 1. 分析订单调查日志 | 用 WorkBuddy 画出 A1024 的模型和工具调用轨迹，并汇总各次模型响应的 Token 用量。 | [A1024 完整会话 JSON](materials/session-trajectory.json) |
| 2. 计算 KV Cache 节省的工作量 | 算出有缓存和无缓存时处理的 Token 位置数，再算节省比例。 | |
| 3. 估算模型部署显存 | 查模型参数，估算权重、KV Cache 和预留空间，判断一张 80 GB 卡能否部署 Qwen3-32B。 | |
| 4. 在 CPU 上部署模型 | 用 vLLM 启动 Qwen3-0.6B，发出一条请求并确认收到有效响应。 | 见下方部署步骤和[启动配置](materials/serve-demo.yaml) |
| 5. 测量并分析性能基线 | 运行压测，记录成功率、吞吐和 P95 延迟，用数据写出一项发现。 | [性能测试脚本](materials/bench.py)和[固定的 20 条请求](materials/requests.jsonl) |
| 6. 调参并复测 | 只改一项服务参数，比较吞吐、成功率和延迟，决定是否保留改动。 | 沿用练习 5 的测试脚本、请求和基线报告 |
| 7. 计算整单 API 费用 | 用课件费率计算逐次费用、整单费用和输入全命中时的理论费用。 | 沿用练习 1 的 JSON，读取各次响应的 `usage` |
| 8. 用 WorkBuddy 优化订单调查助手 | 按课堂方法优化 Demo，提交优化后的模型调用次数、输入 Token 数和输出 Token 数。 | `lesson4-optimized` 分支 |

练习 5 先修改 [压测配置](config/bench.json)，再从项目根目录运行 `python3 materials/bench.py`。练习 8 从 `main` 分支出发，讲评时切到 `lesson4-optimized` 分支的工作目录，再运行 `python3 -m order_agent.app --config config/optimized.json --order A1024` 对照参考实现。

## 浏览器应用

在本目录运行 `python3 -m order_agent.web`，然后打开 http://127.0.0.1:8080 。页面支持订单选择、调查结论和工具证据展开查看。默认离线演示；连接模型使用 `python3 -m order_agent.web --config config/api.json`。可用 `--port 8081` 更换端口。

## 快速开始

在本目录运行：

```sh
python3 -m order_agent.app
python3 -m order_agent.analyze traces/<运行输出的文件名>-session-trajectory.json
python3 -m unittest discover -s tests -v
```

`main` 默认运行优化前版本，`lesson4-optimized` 默认运行优化后参考实现。两者都记录 JSONL，覆盖 A1024 运输延误、A1025 未出库、A1026 证据冲突。

## 连接模型服务或API

```sh
python3 -m order_agent.app --config config/api.json
```

在 `main` 默认读取 `config/local.json`，在参考分支默认读取 `config/optimized.json`。可通过配置文件指定真实模型服务。模型地址、模型名、生成参数、超时、轮数上限及trace目录统一在配置文件管理；trace目录相对配置文件解析。业务输入仍可用 `--order A1025` 指定。

API密钥通过环境变量LLM_API_KEY提供，不写入trace。模型端点必须支持Chat Completions工具调用；vLLM的工具调用解析器需与模型及安装版本匹配。应用支持一轮多个工具调用，当前逐个执行；并行执行是课4练习。网络调用不自动重试，错误被记录；工具错误回传模型，最大12轮防止无界循环。

## 代码阅读路线

- `order_agent/app.py`：请求组装、模型响应、工具结果写回；`History.write` 写入单条事件。完整实际请求与响应、关联ID、工具结果、用量和错误写入JSONL。
- `order_agent/tools.py`：12个mock工具及真实格式JSON Schema。
- `materials/orders.json`：三个合成订单，固定业务时间，不依赖当天日期。
- `order_agent/client.py`：离线脚本与真实API客户端。
- `order_agent/analyze.py`：逐次context的内容体积与API实际usage。字符数不是token数；usage不可用时保留null。工具内容可由tool_call_id追溯来源，尚未实现精确分段token归因。

## 业务设计与课程衔接

教学基线：查订单→仓库→物流→检索政策→核对全文→复查物流→回答。设计要求全文核对和最终物流复查，因此重复工具不直接视为bug；课4可以研究在不损失正确性的情况下改变设计。

课1：用保存的 Session History 还原调用序列并与设计核对；课2：用实际长度分布分析资源需求；课3：连接真实vLLM服务进行测量和参数实验；课4：合并独立工具、缩减内容、复用及路由，并保留对照。

生产案例背景为每副本8张H100 SXM 80GB、BF16 235B模型，5 台服务器；这是课程案例的规模，本地演示可用 Mock 后端。缓存实际命中由推理服务决定。真实部署和实验需有GPU环境、明确质量/延迟标准及版本核验。

所有数据合成。trace包含完整业务内容，仅在mock数据上直接使用；接真实客户数据前需实现脱敏及访问控制。应用完成状态不等于答案质量通过，应对照订单证据和政策人工评估。

## Mock调用等待

配置文件中的`mock.model_delay_seconds`与`mock.tool_delay_seconds`分别设置随机等待区间（秒），默认模型0.3–0.9秒、工具0.05–0.2秒。等待发生在实际mock调用内，由logging与session history记录实际经过时间；这只是教学模拟，不是GPU性能数据。设置为`[0, 0]`可关闭等待。APIClient不会插入模型延迟；当前业务工具仍是mock。

[完整会话 JSON](materials/session-trajectory.json)来自订单助手实际运行 Mock 后端的记录，运行时自动把估算用量写入响应的 `usage`，供第 1、7 项练习使用。接真实模型时读取服务实际返回的用量。

## 课 3 · 测量和调整 vLLM

`materials/` 目录附 20 条合成订单请求、CPU 启动配置和 vLLM 测试入口。请在课程准备好的 Linux CPU 主机上运行，两个终端使用同一个 vLLM 环境。

1. 在项目目录启动服务。若使用预置模型，先将 YAML 的 `model` 改成模型目录，保留 `served-model-name`。
   ```sh
   VLLM_CPU_KVCACHE_SPACE=1 vllm serve --config materials/serve-demo.yaml
   ```
2. 保持 CPU 服务运行。修改 `config/bench.json`，把 `base_url` 指向你部署的接口（包含 `/v1`），把 `model` 填为服务端对外的模型名（`served-model-name`）。然后回到项目根目录运行：
   ```sh
   python3 materials/bench.py
   ```
3. 抄下成功数与失败数，用成功数除以两者之和。再记录 Request throughput（条／秒）、P95 TTFT、P95 流式片段间隔、P95 E2EL（毫秒）。首次运行默认写入 `materials/results/baseline.json`。再次运行可额外指定报告名，已有报告会保留。
4. 调参练习。保留基线报告，复制启动 YAML，把 `max-num-seqs` 从 2 改成 4。停掉旧服务，以新配置启动同一个模型，再运行 `python3 materials/bench.py candidate`。对照吞吐、成功率和三项 P95，给出保留或回退的理由。若服务启动失败，恢复原配置并记录原因。重跑时用新的报告名。

客户端固定最多 4 条并发、`requests.jsonl` 里的 20 条合成订单提示词和 32 个输出 Token 的上限，方便观察服务端调参的影响。脚本只用 Python 标准库。TTFT 按首个可见文本片段计时。单个流式片段可能包含多个 Token，片段间隔用 `p95_chunk_gap_ms` 报告。20 条请求的结果用于课堂比较，无法代表生产容量。样本只访问模型 API，无需启动订单助手或业务工具。

## 练习 8 · Agent 优化

同一订单在改动前后各跑一次，保留两份结果。CLI 和浏览器每次处理请求都会在日志目录生成轨迹 JSON，CLI 也可以指定路径。

```sh
# 改代码前
python3 -m order_agent.app --order A1024 --trajectory traces/baseline.json
# 改代码后
python3 -m order_agent.app --order A1024 --trajectory traces/optimized.json
```

对照两份 JSON 的 `summary`，报告 `model_calls`、`input_tokens` 和 `output_tokens`。先确认两次都完成且 `token_source` 相同。API 使用服务返回的原始用量。离线 Mock 在汇总层以 JSON 字节数估算 Token，两版用同一口径；逐次响应仍保留原样。练习 1 和 7 的样例含单独标注的课堂模拟用量，用于读日志和算费用。


发给 WorkBuddy 的任务：

> 请用同样的 A1024、A1025、A1026 跑优化前后两版，保留自动生成的轨迹 JSON。选择一项减少调用和一项减少单次用量的改动。逐单给出模型调用次数，再汇总整单输入和输出 Token。A1024 核对预计送达日，A1025 核对未出库，A1026 核对冲突升级。

每次发出模型请求计一次，回退的模型调用单独计入。逐次汇总输入和输出 Token，输入包含缓存命中部分。API 用实际 usage。Mock 使用运行时轨迹里的估算值，报告里注明估算口径。

### 参考实现

参考实现位于 `lesson4-optimized` 分支。课堂讲评可另开一个工作目录，保留学员当前修改。

```sh
git worktree add ../fde-xiaozhi-order-agent-reference lesson4-optimized
cd ../fde-xiaozhi-order-agent-reference
```

在参考实现目录运行：

```sh
python3 -m order_agent.app --config config/optimized.json --order A1024
python3 -m order_agent.web --config config/optimized.json --port 8081
python3 -m materials.compare
```

- `config/local.json` 默认运行基线，`config/optimized.json` 打开参考优化。两份配置都使用 Mock。
- `order_agent/optimization.py` 中，应用先查订单，并用返回的运单号取初始物流。模型在一次响应里提出独立查询。政策正文保留 ID 和正文，原始工具结果继续写入日志。
- 固定系统指令在前，业务日期随订单上下文发送。准备好证据后，末次请求清空工具并按四项要求答复。课堂参考配置全程使用相同的 Qwen3-235B-A22B 模型标识。
- `python3 -m materials.compare` 对两版使用同一旗舰模型标识作为取证基线。它保留两个流程的调用、请求字符数、末轮工具数和答复对照。输入字符数不是 Token 数。缓存命中、账单和真实模型质量需要在线复测。
- 若有合适的 API，在 `config/` 下复制 `optimized.json`，将新配置的 `llm.backend` 改成 `api`，并通过 `LLM_API_KEY` 提供凭证。再复制一份 API 配置并删除 `agent.optimization` 作为在线基线。两版用同一模型端点和价目。清空工具的请求带历史工具消息，先验证服务端兼容性。

参考分支保留 Qwen 分词器供离线复算。在该分支安装 `tokenizers` 和 `jinja2` 后，运行 `python3 -m materials.measure_step_tokens`，用随项目提供的 Qwen 分词器复算三笔样例的模型调用次数、输入 Token 和输出 Token。


### 会话、交互轮次与执行步骤

`task_id` 标识本次演示会话，`turn` 为用户发起的交互轮次。一笔订单从提问到最终答复是一轮；每次模型或工具执行使用 `step_id` 标识，`model_call_index` 表示该轮内第几次模型调用。同一次模型调用的请求与响应共享同一个步骤 ID。

- [政策原文件](materials/order-delay-policy.md)由 `get_policy_document` 原样读出。参考实现保留完整工具结果用于诊断，只把政策编号和正文发送给模型。
- [同一订单的第二次基线回放](materials/session-trajectory-later.json)通过 `--processing-time "2026-10-30 14:40"` 生成，与第一次回放对比首条请求的 System 前缀。
- 这些轨迹运行的是 Mock，使用 Qwen3-235B-A22B 的模型标识。用量按序列化长度估算，缓存栏模拟 128 Token 块的前缀复用。实际服务的 Token 计数、缓存命中与费用以服务返回值为准。

从基线配置复现第 4 课的单项对照：

```sh
python3 -m order_agent.app --config config/local.json --order A1024 --trim-policy --trajectory traces/a1024-trimmed.json
python3 -m order_agent.app --config config/local.json --order A1024 --trim-policy --compact-reply --trajectory traces/a1024-compact.json
python3 -m order_agent.app --config config/local.json --order A1024 --stable-prefix --trajectory traces/a1024-stable.json
python3 -m order_agent.app --config config/local.json --order A1024 --stable-prefix --processing-time "2026-10-30 14:40" --trajectory traces/a1024-stable-later.json
```

对照文件也在 `materials/`。精简政策比较第 6、7 次请求，四项答复比较第 7 次响应，前缀比较两次会话的第 1 次请求。
