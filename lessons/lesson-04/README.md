# 课 4：Agent 成本优化

[练习输入与参考答案](materials/exercises.md)

[合并讲师脚本](lesson-04-script.md)，34 页。

- **P01–P07 核算基线**：用第 1 课的 A1024 执行轨迹和用量，计算整笔费用。
- **P08–P31 八项应用优化**：每项三页，先分析具体请求或工具记录，再讲优化思路，最后给一条可直接发给 WorkBuddy 的操作样例。
- **P32–P34 复测与总结**：对照参考实现，用 WorkBuddy 动手优化同一个 Demo，再回顾全天四课。

[第 38 版 PPT](pptx/output/lesson-04-v38.pptx)与现行讲稿对应。

## 教学材料

- [第 1 课原始会话记录](../lesson-01/materials/session-history.jsonl) · [调用序列](../lesson-01/materials/call-sequence.mmd)
- [第 1 课会话 JSON 中的教学用量](../lesson-01/materials/session-history.json) · [WorkBuddy 成本练习与答案](materials/api-cost-exercise.md)
- [原始七次调用的离线输入](materials/baseline-context-analysis.csv) · [工具依赖图](materials/tool-dependencies.mmd)
- [六次调用的离线输入](materials/a1024-multi-tool-inputs.json) · [六次调用的复跑脚本](scripts/replay_multi_tool.py) · [政策资料截图](materials/policy-document-preview.png)
- [优化实验与代码入口](materials/application-experiments.md) · [验收样例](materials/acceptance-cases.json) · [复测记录空表](materials/experiment-record.csv)

同一份含 PDF 前置页的政策返回下，A1024 原七次调用共 11,527 个离线输入 token。首轮同查订单与仓库后为 6 次、10,040 个输入 token。再过滤前置页，整单降至 9,630。模拟账本的命中量与输出量用于演算。真实 API 费用以服务商用量为准，生产质量、延迟和自建容量以目标环境复测为准。
