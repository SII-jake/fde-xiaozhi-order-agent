# 日志与用量的来源

- [原始 JSONL](session-history.jsonl)来自教学项目运行 A1024 时的实际 Mock 输出。[会话 JSON](session-history.json)把同一份事件放在一个对象里，方便阅读。请求和响应保留原始字段，Mock 的 `usage` 为 `null`。
- [完整服务日志](lesson1-end-service.log)与会话来自同一次运行。[初始日志](service-run.log)来自单独一次运行。等待时长由 Mock 配置随机生成，时间戳记录的是本地运行时间。
- [会话 JSON](session-history.json)中的 `teaching_usage.calls`使用离线分词复算输入量，缓存命中与输出量用于课堂费用演算。
- 合成业务日期固定为 2026-10-29。
