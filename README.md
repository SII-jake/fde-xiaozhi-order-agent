# 小智的订单调查助手

独立的学员Git项目，Python 3.10+，运行不需要第三方依赖。业务工具全部mock，无真实退款、消息或工单提交。

## 快速开始

在本目录运行：

```sh
python3 -m order_agent.app --trace traces/example.jsonl
python3 -m order_agent.analyze traces/example.jsonl
python3 -m unittest discover -s tests -v
```

trace文件不覆盖已有文件，请换新名称。默认mock是确定性的脚本流程，不是真模型、不用于性能或质量结论，也不虚构token usage。三个订单：A1024运输延误、A1025未出库、A1026证据冲突。mock固定七轮用于教学对照，真实模型自行选择12个工具，不要求全用。

## 连接模型服务或API

```sh
python3 -m order_agent.app --backend api --base-url http://localhost:8000/v1 --model Qwen/Qwen3-235B-A22B-Instruct-2507
```

API密钥通过环境变量LLM_API_KEY提供，不写入trace。模型端点必须支持Chat Completions工具调用；vLLM的工具调用解析器需与模型及安装版本匹配。应用支持一轮多个工具调用，当前逐个执行；并行执行是课4练习。网络调用不自动重试，错误被记录；工具错误回传模型，最大12轮防止无界循环。

## 代码阅读路线

- `order_agent/app.py`：请求组装、模型响应、工具结果写回；`History.write`是课1定位记录代码的位置。完整实际请求与响应、关联ID、工具结果、用量和错误写入JSONL。
- `order_agent/tools.py`：12个mock工具及真实格式JSON Schema。
- `data/orders.json`：三个合成订单，固定业务时间，不依赖当天日期。
- `order_agent/client.py`：离线脚本与真实API客户端。
- `order_agent/analyze.py`：逐次context的内容体积与API实际usage。字符数不是token数；usage不可用时保留null。工具内容可由tool_call_id追溯来源，尚未实现精确分段token归因。

## 业务设计与课程衔接

教学基线：查订单→仓库→物流→检索政策→核对全文→复查物流→回答。设计要求全文核对和最终物流复查，因此重复工具不直接视为bug；课4可以研究在不损失正确性的情况下改变设计。

课1：读取conversation history并与设计核对，逐调用观察context；课2：用实际长度分布分析资源需求；课3：连接真实vLLM服务进行测量和参数实验；课4：合并独立工具、缩减内容、复用及路由，并保留对照。

生产案例背景为每副本8张H100 SXM 80GB、BF16 235B模型，12副本；这不是本地demo的硬件要求。12→8→5只是待验证假设。本项目尚不提供GPU压测、部署自动化、前缀缓存或模型路由实现，不能宣称已经验证省机器效果。真实部署和实验需有GPU环境、明确质量/延迟标准及版本核验。

所有数据合成。trace包含完整业务内容，仅在mock数据上直接使用；接真实客户数据前需实现脱敏及访问控制。应用完成状态不等于答案质量通过，应对照订单证据和政策人工评估。
