# 课 3 备课笔记 · vLLM 部署与优化

P07 在 CPU 主机上用 Qwen3-0.6B 验证部署和接口。P08 回到课 1 的发现，5 台机器都在用，小智还缺峰值下单台能完成多少请求的数据。P14 用固定样本实测 CPU 基线，P46 只改一个服务端参数再测。小智的八卡案例用模拟数据演练容量分析。

## 多 GPU 部署概念

P03 用五层图从订单请求展开到单卡，在同一张图里标出层内分工。DP 分请求，PP 按层分阶段，TP 切分同一层的张量，EP 在 MoE 层按专家分卡。图中的模型副本、阶段和卡数用于解释分工。[vLLM 并行与扩展](https://docs.vllm.ai/en/stable/serving/parallelism_scaling/)

## 先定义容量

- 模型服务记录发送速率、完成吞吐、TTFT、ITL、完整调用延迟和错误。持续的发送与完成差异要结合队列、失败和取消解释。
- 按客服整单等待和调查质量确定门槛，回放完整订单验证。压模型服务用代表性的单次请求分布，固定模型、硬件、模板、精度和负载。
- 用最后一个稳定达标点的完成速率估算容量，结合峰值、负载偏斜和故障余量复测候选机器数。

## 配置与对照

| 观察 | vLLM 配置 | 对照 |
|---|---|---|
| 排队增长，运行序列数到上限，KV 还有空间 | `max-num-seqs` | 只改运行序列上限，比较达标吞吐、延迟和抢占 |
| 长输入打断正在生成的请求 | `enable-chunked-prefill`、`max-num-batched-tokens` | 两档 每轮 token 数上限，比较 TTFT 和 ITL；必要时再评估 P/D 分离 |
| 高峰反复 KV 抢占，尾延迟或达标吞吐退化 | 有显存余量时试 `gpu-memory-utilization`，余量不足时试 `max-num-seqs` | 小智显式设 0.90，stable 文档列 0.92。KV 池默认自动估算，看启动容量和抢占增量。显式 `kv-cache-memory-bytes` 覆盖自动估算。 [vLLM 参数](https://docs.vllm.ai/en/stable/cli/serve/#--gpu-memory-utilization) |
| 低并发下生成间隔长 | 兼容量化 checkpoint、`quantization` 或 `speculative-config` | 先确认瓶颈，再看质量、接受率、ITL 和达标吞吐；KV 精度另用 `kv-cache-dtype` |
| Prefill 和 Decode 需要独立部署 | `kv-transfer-config` 与兼容的 KV connector | 同样的 GPU 预算，对比队列、KV 传输和达标吞吐 |
| 实际请求出现大量相同长前缀 | `enable-prefix-caching` | P31–P33。先确认最终 token 序列的共同前缀，只切换缓存开关，固定请求与发送节奏，比较命中 token 占比、P95 TTFT 和达标吞吐 |
| 多轮长调查换模型副本后重复计算前缀 | 两组都开前缀缓存，比较网关的负载路由与缓存感知路由 | P34–P36。固定模型副本和流量，比较各模型副本队列、命中 token、P95 TTFT 和达标吞吐。实际配置参考 [Production Stack](https://docs.vllm.ai/projects/production-stack/en/vllm-stack-0.1.13/use_cases/loadaware-routing.html) |

[调优指南](https://docs.vllm.ai/en/latest/configuration/optimization/) · [服务参数](https://docs.vllm.ai/en/latest/cli/serve/) · [专家并行](https://docs.vllm.ai/en/latest/serving/expert_parallel_deployment/) · [P/D 分离](https://docs.vllm.ai/en/latest/features/disagg_prefill/) · [前缀缓存](https://docs.vllm.ai/en/latest/features/automatic_prefix_caching/)

用 [CPU YAML](../../../lesson3/serve-demo.yaml) 准备课堂实测环境，详见[环境记录](environment-record.md)。[八卡 YAML](serve-case.yaml)用于多卡技术与容量算例。
