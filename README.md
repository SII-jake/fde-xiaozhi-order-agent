# 小智的订单调查助手

独立的学员Git项目，Python 3.10+，运行不需要第三方依赖。业务工具全部mock，无真实退款、消息或工单提交。

## 课程资料

[课程方案](course-plan.md) · [课堂练习与参考答案](classroom-exercises.md)

| 课程 | 讲稿、课件和材料 |
|---|---|
| 课程简介与第 1 课 · Agent 与可观测性 | [第 1 课](lessons/lesson-01/README.md) · [A1024 完整会话 JSON](lessons/lesson-01/materials/session-history.json) |
| 第 2 课 · 大模型原理 | [第 2 课](lessons/lesson-02/README.md) |
| 第 3 课 · 推理引擎部署与优化 | [第 3 课](lessons/lesson-03/README.md) · [CPU 部署手册](lessons/lesson-03/materials/vllm-deployment-lab.docx) |
| 第 4 课 · Agent 成本优化 | [第 4 课](lessons/lesson-04/README.md) |

## 浏览器应用

在本目录运行 `python3 -m order_agent.web`，然后打开 http://127.0.0.1:8080 。页面支持订单选择、调查结论和工具证据展开查看。默认离线演示；连接模型使用 `python3 -m order_agent.web --config config/api.json`。可用 `--port 8081` 更换端口。

## 快速开始

在本目录运行：

```sh
python3 -m order_agent.app
python3 -m order_agent.analyze traces/<运行输出的文件名>.jsonl
python3 -m unittest discover -s tests -v
```

本分支默认从 `config/optimized.json` 加载第 4 课参考实现，记录完整 JSONL。离线 Mock 演示 A1024 运输延误、A1025 未出库、A1026 证据冲突。用 `--config config/local.json` 可在本分支复跑基线。

## 连接模型服务或API

```sh
python3 -m order_agent.app --config config/api.json
```

默认读取 `config/optimized.json`（离线 Mock）。连接真实 API 的配置方式见[第 4 课实操](lesson4/README.md)。模型地址、模型名、生成参数、超时、轮数上限及trace目录统一在配置文件管理；trace目录相对配置文件解析。业务输入仍可用 `--order A1025` 指定。

API密钥通过环境变量LLM_API_KEY提供，不写入trace。模型端点必须支持Chat Completions工具调用；vLLM的工具调用解析器需与模型及安装版本匹配。应用支持一轮多个工具调用，当前逐个执行；并行执行是课4练习。网络调用不自动重试，错误被记录；工具错误回传模型，最大12轮防止无界循环。

## 代码阅读路线

- `order_agent/app.py`：请求组装、模型响应、工具结果写回；`History.write` 写入单条事件。完整实际请求与响应、关联ID、工具结果、用量和错误写入JSONL。
- `order_agent/tools.py`：12个mock工具及真实格式JSON Schema。
- `data/orders.json`：三个合成订单，固定业务时间，不依赖当天日期。
- `order_agent/client.py`：离线脚本与真实API客户端。
- `order_agent/analyze.py`：逐次context的内容体积与API实际usage。字符数不是token数；usage不可用时保留null。工具内容可由tool_call_id追溯来源，尚未实现精确分段token归因。

## 业务设计与课程衔接

教学基线：查订单→仓库→物流→检索政策→核对全文→复查物流→回答。设计要求全文核对和最终物流复查，因此重复工具不直接视为bug；课4可以研究在不损失正确性的情况下改变设计。

课1：用保存的 Session History 还原调用序列并与设计核对；课2：用实际长度分布分析资源需求；课3：连接真实vLLM服务进行测量和参数实验；课4：合并独立工具、缩减内容、复用及路由，并保留对照。

生产案例背景为每副本8张H100 SXM 80GB、BF16 235B模型，5 台服务器；这是课程案例的规模，本地演示可用 Mock 后端。缓存实际命中由推理服务决定。真实部署和实验需有GPU环境、明确质量/延迟标准及版本核验。

所有数据合成。trace包含完整业务内容，仅在mock数据上直接使用；接真实客户数据前需实现脱敏及访问控制。应用完成状态不等于答案质量通过，应对照订单证据和政策人工评估。

## Mock调用等待

配置文件中的`mock.model_delay_seconds`与`mock.tool_delay_seconds`分别设置随机等待区间（秒），默认模型0.3–0.9秒、工具0.05–0.2秒。等待发生在实际mock调用内，由logging与session history记录实际经过时间；这只是教学模拟，不是GPU性能数据。设置为`[0, 0]`可关闭等待。APIClient不会插入模型延迟；当前业务工具仍是mock。

第 1 课用预先录制的日志对照初始服务日志和完整会话。样例及运行来源见[第 1 课](lessons/lesson-01/README.md)。

## 课 4 · 优化前与参考实现

学员在 `main` 分支从优化前版本开始。`lesson4-optimized` 分支提供优化后的参考实现。切换方式、运行入口和结果见[第 4 课实操](lesson4/README.md)。

## 课 3 · 测量和调整 vLLM

`lesson3/` 目录附 20 条合成订单请求、CPU 启动配置和 vLLM 测试入口。请在课程准备好的 Linux CPU 主机上运行，两个终端使用同一个 vLLM 环境。

1. 在项目目录启动服务。若使用预置模型，先将 YAML 的 `model` 改成模型目录，保留 `served-model-name`。
   ```sh
   VLLM_CPU_KVCACHE_SPACE=1 vllm serve --config lesson3/serve-demo.yaml
   ```
2. 保持服务运行，在同一台机器另开终端，回到项目目录跑基线。如果使用本地模型目录，先在第二个终端执行 `export LAB_MODEL=/path/to/model`，与 YAML 中的 `model` 一致。
   ```sh
   bash lesson3/bench.sh baseline
   ```
3. 抄下成功数与失败数，用成功数除以两者之和。再记录 Request throughput（条／秒）、P95 TTFT、P95 ITL、P95 E2EL（毫秒）。JSON 报告在 `lesson3/results/`。
4. 调参练习。保留基线报告，复制启动 YAML，把 `max-num-seqs` 从 2 改成 4。停掉旧服务，以新配置启动同一个模型，再运行 `bash lesson3/bench.sh candidate`。对照吞吐、成功率和三项 P95，给出保留或回退的理由。若服务启动失败，恢复原配置并记录原因。重跑时用新的报告名。

客户端固定最多 4 条并发、同一批输入和 32 个输出 token 的上限，方便观察服务端调参的影响。20 条请求的结果用于课堂比较，无法代表生产容量。样本只访问模型 API，无需启动订单助手或业务工具。
