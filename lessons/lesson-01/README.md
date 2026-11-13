# 课 1：Agent 与可观测性

[练习输入与参考答案](materials/exercise.md)

[合并讲师脚本](lesson-01-script.md)

讲稿和[第 34 版 PPT](pptx/output/lesson-01-v34.pptx)共 28 页，课程简介和第 1 课连续编号。

- **P01–P05 课程简介**：讲师介绍、课程动机、全天安排与课前准备。
- **P06–P10 背景**：小智接到降本任务，沿 A1024 调查路线了解助手，核对五台 GPU 服务器的请求和业务增长。
- **P11–P19 Agent 可观测性**：先讲 Agent 与工具如何执行任务，再介绍可观测性，对照 Run、Trace、Thread 与 Span、Turn、Session，后续统一使用会话、交互轮次和执行步骤。
- **P20–P22 平台与自行采集**：通过 Langfuse 官方截图讲成本看板和执行轨迹，再讲应用入口、模型调用与工具执行的记录点。
- **P23–P25 调用取证**：按会话、交互轮次和执行步骤标出旧日志缺口，再打开完整 A1024 JSON。
- **P26–P27 小练习与核对**：用 WorkBuddy 画出 Agent 轨迹并统计用量，将统计结果交给第 4 课计算费用。
- **P28 复核与交接**：对照 P08 和实际调用序列，核对政策查询、物流复查和调用状态，引入第 2 课。

练习使用[完整观测 JSON](materials/session-history.json)（教学用量在同一文件的 `teaching_usage.calls`）。

## 日志样例与参考答案

- [初始服务日志](materials/service-run.log)只有任务和模型调用事件。
- [完整服务日志](materials/lesson1-end-service.log)、[原始 JSONL](materials/session-history.jsonl)和[便于阅读的 JSON](materials/session-history.json)来自同一次 A1024 Mock 回放。[采集说明](materials/service-run-provenance.json)记录了日志来源与模拟耗时口径。
- [调用序列图](materials/call-sequence.mmd)和[练习复算代码](scripts/analyze_exercise.py)用于课堂核对。
- 课件图标来自 Lucide，见[来源说明](materials/icons/README.md)及[许可](materials/icons/LICENSE)。
