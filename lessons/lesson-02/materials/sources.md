# 来源与数字口径

核对日期：2026-11-04。在线main页面可能继续变化，课3实验需固定revision和软件版本。

| 用途 | 一手来源 | 讲稿位置 |
|---|---|---|
| GPU状态字段与读图 | [NVIDIA nvidia-smi官方说明](https://docs.nvidia.com/deploy/nvidia-smi/index.html) | P03，截图待讲师提供 |
| 总参数/激活参数、模型结构 | [Qwen官方模型卡](https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507) | P30、P14～P14 |
| 全网络原始权重大小 | [官方权重索引](https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507/raw/main/model.safetensors.index.json) | P08，按结构计算后与total_size核对 |
| 94层、4个KV头、head_dim128、BF16等 | [官方config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507/raw/main/config.json) | P04、P15 |
| Transformer背景 | [Attention Is All You Need](https://arxiv.org/abs/1706.03762) | P04～P05 |
| GQA与KV头区别 | [GQA论文](https://arxiv.org/abs/2305.13245) | P15 |
| KV的含义与复用 | [Transformers缓存说明](https://huggingface.co/docs/transformers/main/en/cache_explanation) | P13 |
| H100 SXM标称80GB与互连 | [NVIDIA官方规格](https://www.nvidia.com/en-us/data-center/h100/) | P09 |
| GPU计算与带宽限制 | [NVIDIA GPU性能背景指南](https://docs.nvidia.com/deeplearning/performance/dl-performance-gpu-background/index.html) | P02、P22 |
| KV分页管理背景 | [PagedAttention论文](https://arxiv.org/abs/2309.06180) | P21 |
| 多卡KV复制的条件化例子 | [vLLM Qwen3Attention实现](https://raw.githubusercontent.com/vllm-project/vllm/main/vllm/model_executor/models/qwen3.py) | P16备注，具体课堂后端待定 |

## 本课自己推导的数字

参数粗估使用235×10⁹，权重BF16为每参数2字节：470GB≈437.72GiB。8张卡的640GB是标称量级，差额170GB还需扣运行时、KV及其他开销，不能当作实测可用空间。

逻辑KV假设：标准全注意力、BF16 KV、无跨请求共享，2×94×4×128×2＝192,512字节/token，即188KiB/token。8K指8,192，32K指32,768；分别约1.46875GiB、5.875GiB/序列。不是把262,144的模型原生最大位置当作课程32K配置，也不是让所有短请求都占满32K。

每TP rank至少保留一个KV头的条件下，TP8相对4个逻辑KV头出现两倍合计复制；实际后端与缓存报告仍须核对。不把逻辑KV平均除以8当作真实每卡容量。

这些是物理量估算，没有使用GPU跑分。没有用NVIDIA的稀疏峰值算力推真实token/s，没有用显存总带宽除以235B权重预测本MoE服务速度，也没有写输出API价格由物理比例决定。

## 原始课稿的使用范围

原始 Transformer 备课稿只作为历史备课参考。其27B/32B演算不再混入本案例；‘所有权重必须常驻’、‘decode每步读取全部权重’、‘输入必算力/输出必带宽’、‘由规格直接得到并发或速度’等绝对化表述不沿用。

## 部署显存公式练习参考

用户提供的《从零搭建产品功能问答助手-脱敏.pptx》第38～42页提供（权重＋KV）×1.2公式与单并发32K练习形式，第43页采用Qwen3-0.6B部署。本课P18先介绍model card与配置查找；P19～P20用该小模型完成单卡估算，不再采用235B模型及TP8复制系数。1.2是课堂假设。

小模型的一手来源：[官方模型卡](https://huggingface.co/Qwen/Qwen3-0.6B)、[官方配置](https://huggingface.co/Qwen/Qwen3-0.6B/raw/main/config.json)，核对日期2026-11-04。总参数约0.6B、28层、8个KV头、head_dim128。题设FP16权重与KV均2字节，单并发32,768缓存token，总估算约5.95GB；4并发约19.48GB。默认配置BF16与题设精度明确区分，配置最大位置与题设32K也明确区分。

网络图新增细分预算由`calculate_network_memory.py`从BF16张量形状推导，未加载模型。Embedding和输出头各1,244,659,712字节；每层Attention为142,606,336字节，专家及路由器合计4,832,886,784字节，归一化合计16,896字节。94层加最终归一化后总计470,187,269,120字节，与官方索引一致。单份32K×4096的BF16隐藏状态为256MiB，不代表所有激活或实际运行时峰值。
