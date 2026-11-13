# 课堂练习与配套材料

| 练习 | 要求 | 发放材料 |
|---|---|---|
| 1. 分析订单调查日志 | 用 WorkBuddy 画出 A1024 的模型和工具调用轨迹，再汇总同一文件中的教学 Token 用量。 | [A1024 完整会话 JSON](lessons/lesson-01/materials/session-history.json) |
| 2. 计算 KV Cache 节省的工作量 | 算出有缓存和无缓存时处理的 Token 位置数，再算节省比例。 | 用课件题目 |
| 3. 估算模型部署显存 | 查模型参数，估算权重、KV Cache 和预留空间，判断一张 80 GB 卡能否部署 Qwen3-32B。 | 用课件条件和模型卡 |
| 4. 在 CPU 上部署模型 | 用 vLLM 启动 Qwen3-0.6B，发出一条请求并确认收到有效响应。 | [CPU 部署手册](lessons/lesson-03/materials/vllm-deployment-lab.docx) |
| 5. 测量并分析性能基线 | 运行压测，记录成功率、吞吐和 P95 延迟，用数据写出一项发现。 | [性能测试脚本](lesson3/bench.sh)和[固定的 20 条请求](lesson3/requests.jsonl) |
| 6. 调参并复测 | 只改一项服务参数，比较吞吐、成功率和延迟，决定是否保留改动。 | 沿用练习 5 的测试脚本、请求和基线报告 |
| 7. 计算整单 API 费用 | 用课件费率计算逐次费用、整单费用和输入全命中时的理论费用。 | 沿用练习 1 的 JSON，读取 `teaching_usage.calls` |
| 8. 用 WorkBuddy 优化订单调查助手 | 按课堂方法优化 Demo，提交优化后的模型调用次数、输入 Token 数和输出 Token 数。 | [操作和运行说明](lesson4/README.md) · `lesson4-optimized` 分支 |

练习 5 从项目根目录运行 `bash lesson3/bench.sh baseline`。练习 8 从 `main` 分支出发，讲评时切到 `lesson4-optimized` 分支的工作目录，再运行 `python3 -m order_agent.app --config config/optimized.json --order A1024` 对照参考实现。
