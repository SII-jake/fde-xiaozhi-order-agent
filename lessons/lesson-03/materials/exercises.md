# 第 3 课 CPU 部署与性能练习

| 页 | 学员输入 | 提交 |
|---|---|---|
| P07 部署 | [部署手册](vllm-deployment-lab.docx)、[CPU 启动配置](../../../lesson3/serve-demo.yaml)、[请求样例](smoke-request.json) | 模型 ID、配置和一次成功响应 |
| P14 基线 | 学员项目的[固定 20 条请求](../../../lesson3/requests.jsonl)、[压测脚本](../../../lesson3/bench.sh) | baseline.json 和用数字说明的分析 |
| P46 调参 | 相同请求集、并发 4、原基线 | 候选配置、复测 JSON 和取舍结论 |

## 参考答案

- 部署成功时，/v1/models 可找到 order-demo-0.6b，发送 smoke 请求能收到非空内容。答复原文随模型和设置而异。
- [示例基线](cpu-report-example.json)和[示例候选](cpu-report-tuned-example.json)均为教学构造。基线完成 20/20，吞吐 1.6 条/秒，P95 TTFT 为 1,950 ms。单个并发档只能说明这一档的表现。
- 候选吞吐提高到 1.9 条/秒，首字等待缩短，后续间隔和端到端延迟却增加。实际是否接受，要先看业务延迟门槛，再用同一批请求复测。课堂可把 max-num-seqs 从 2 改到 4 作为候选，按学员自己的报告做判断。
- [报告对比代码](../scripts/compare_cpu_reports.py)接收基线和候选 JSON，逐项列出差值。默认按 20 条请求计算成功率。
