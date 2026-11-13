# 部署与测量环境记录

| 项目 | 课前记录 |
|---|---|
| CPU 主机 | 架构、指令集、内存、CPU 版 vLLM 版本 |
| 模型与配置 | revision、权重目录、模板、服务 YAML |
| 负载和验收 | 代表性订单集、质量、延迟、峰值、错误 |

## CPU 练习

1. 在 Linux x86_64 教学机按官方文档预装 vLLM CPU 构建，核对支持的指令集。预先下载 Qwen3-0.6B，准备依赖和官方说明要求的 OpenMP 环境。[vLLM CPU 安装](https://docs.vllm.ai/en/latest/getting_started/installation/cpu/)
2. 在项目根目录执行 `VLLM_CPU_KVCACHE_SPACE=1 vllm serve --config lesson3/serve-demo.yaml`。1 GiB 是课堂起点，按实际内存验证。
3. 检查 `/v1/models`，再发 `smoke-request.json` 到 `http://127.0.0.1:8000/v1/chat/completions`。记录 `order-demo-0.6b` 与非空回答。选做 `tool-request.json`。

4. 分发学员项目。按[学员手册](vllm-deployment-lab.docx)在教学机验证 P14 的 `bash lesson3/bench.sh baseline` 能输出成功数、吞吐和三项 P95，并保存报告。
5. 预演 P46。只把服务端 `max-num-seqs` 从 2 调到 4，重启后运行 `bash lesson3/bench.sh candidate`，确认两个报告能对照。

## 八卡案例

使用课件的教学模拟数据讲解容量余量和指标取舍。[八卡 YAML](serve-case.yaml)用于说明小智的部署配置。
