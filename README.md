# 小智的订单调查助手

根据订单、仓库、物流和政策记录调查订单延误，给出原因、证据和处理建议。项目提供命令行与浏览器界面。应用和压测脚本使用 Python 3.10+ 标准库。

内置三笔合成订单，可离线运行：A1024 运输延误、A1025 未出库、A1026 证据冲突。业务工具使用模拟数据，工单工具仅生成待确认草稿。

## 快速开始

在项目根目录运行：

```sh
python3 -m order_agent.app "A1024 为什么还没到？"
```

启动浏览器界面：

```sh
python3 -m order_agent.web
```

打开 [订单工作台](http://127.0.0.1:8080)，直接发送包含订单号的问题，例如「A1024 为什么还没到？」。展开工具记录即可查看调查证据。每次调查一笔订单。使用 `--port 8081` 可以更换端口。

## 连接模型服务

在 [API 配置](config/api.json)中填写服务的 `base_url`（包含 `/v1`）和对外模型名。服务需要支持 Chat Completions 工具调用。如需鉴权，通过环境变量 `LLM_API_KEY` 提供密钥。

```sh
python3 -m order_agent.app --config config/api.json "A1024 为什么还没到？"
python3 -m order_agent.web --config config/api.json
```

配置文件还控制生成参数、超时、模型调用轮数上限和轨迹目录。轨迹路径相对于配置文件所在目录解析。Mock 模式使用 [本地配置](config/local.json)，可通过 `mock.model_delay_seconds` 和 `mock.tool_delay_seconds` 调整模拟等待，设为 `[0, 0]` 可关闭。

## 查看执行轨迹

每次调查会生成原始 JSONL 日志和会话轨迹 JSON，包含实际发出的模型请求、响应、耗时、工具参数和结果。CLI 可以指定尚不存在的输出路径：

```sh
python3 -m order_agent.app --trajectory traces/a1024.json "A1024 为什么还没到？"
python3 -m order_agent.analyze traces/a1024.json
```

[完整样例](materials/session-trajectory.json)由 Mock 运行自动生成。一次提问到最终答复是一轮交互（`turn`）；模型调用和工具执行各有自己的步骤 ID（`step_id`）。模型请求和响应共享同一个步骤 ID，`model_call_index` 表示它是该轮的第几次模型调用。

`summary` 汇总模型调用次数、输入 Token 和输出 Token。Mock 的 `usage` 是估算值，API 模式读取服务实际返回的用量。轨迹保留完整业务内容，接入真实业务数据前需配置脱敏和访问控制。

## 测量推理服务性能

可以按 [CPU 部署步骤](materials/vllm-deploy-model.md)启动 vLLM，也可以使用已启动的服务。在 [压测配置](config/bench.json)中填写服务地址和实际模型名，然后运行：

```sh
python3 materials/bench.py
```

脚本使用 [20 条合成订单请求](materials/requests.jsonl)，默认并发 4，每条最多生成 32 Token。预热完成后，报告成功率、请求吞吐、P95 首 Token 延迟、P95 流式片段间隔和 P95 端到端延迟。一个流式片段可能含多个 Token。

报告默认写入 `materials/results/baseline.json`。复测时可用 `python3 materials/bench.py candidate` 生成另一份报告。脚本直接请求模型服务，运行时无需启动订单助手。

## 优化参考实现

当前分支在订单号和权限确认后于同一次模型响应中发出查订单与查仓库两条工具调用，应用执行两条查询并把结果回传模型；首次查物流等查订单带回运单号后进行，随后检索并读取 [政策全文](materials/order-delay-policy.md)，答复前复查物流。`lesson4-optimized` 分支提供参考实现，包含订单与物流预取、合并独立工具调用、精简政策结果、稳定请求前缀和约束最终答复。精简政策时，工具日志仍保留 Markdown 原文。

在参考分支运行：

```sh
python3 -m order_agent.app --config config/optimized.json
python3 -m materials.compare
```

比较两版时使用相同订单、模型和用量口径，核对轨迹 `summary`，再检查预计送达日期、未出库和证据冲突等结论。项目改动从 `main` 开始，修改代码前后各生成一份轨迹。单项优化对照和完整参考实现可在 `lesson4-optimized` 分支查看。

## 项目结构

| 路径 | 用途 |
|---|---|
| `order_agent/app.py` | 命令行入口、模型与工具调用、原始事件记录 |
| `order_agent/web.py` | 浏览器应用入口 |
| `order_agent/client.py` | Mock 和 API 模型客户端 |
| `order_agent/tools.py` | 模拟业务工具与工具定义 |
| `order_agent/trajectory.py` | 会话轨迹导出与用量汇总 |
| `materials/` | 订单数据、政策文件、样例轨迹和压测脚本 |
| `config/` | 应用与压测配置 |

运行测试：

```sh
python3 -m unittest discover -s tests -v
```
