# 课 2：大模型原理

[练习输入与参考答案](materials/exercises.md)

主文档：[合并讲师脚本](lesson-02-script.md)。现行讲稿共 29 页。[第37版PPT](pptx/output/lesson-02-v37.pptx)与现行讲稿对应。

| 内容 | 页码 |
|---|---|
| GPU、监控、显存占用的三类来源 | P01～P05 |
| 订单问题经过的模型模块、参数与 MoE | P06～P08 |
| 逐 Token 生成、JSON 转换、流程总览与注意力重算 | P09～P12 |
| A1024 算例、KV Cache、小练习与批处理 | P13～P18 |
| 并发显存预算、估算公式与数值位宽 | P19～P21 |
| Model Card 查参数与显存小练习 | P22～P23 |
| 两卡张量并行通信算例 | P24 |
| 并发容量、达标条件与 Prefill / Decode | P25～P27 |
| 回顾与交接 | P28～P29 |

网络图保持原位后展开专家；生成与KV部分使用同一条输入和输出、同一执行图布局。删除脱离图示的4/5/6位置练习。

[真实模板、完整分词与编号](materials/tokenizer-example.json)来自目标模型公开tokenizer，已运行并验证可还原；输入共16 token。示例输出“物流延误了。”是讲解安排，不是真实模型答案。只运行分词器，未加载模型权重或测GPU。

[分词复算脚本](scripts/create_token_example.py)需要Python的tokenizers和jinja2；首次下载的公开tokenizer保存在materials/tokenizer/，SHA256在结果JSON内。下载来源为Hugging Face公开文件的hf-mirror镜像。无需模型权重或API密钥。

[课3备课笔记](../lesson-03/materials/vllm-teaching-notes.md)。

## 材料

- [案例模型配置](materials/model-config-excerpt.json)和[案例显存预算](materials/memory-budget.json)支持小智案例的显存讲解。
- [网络权重复算](scripts/calculate_network_memory.py)按案例模型的张量形状核对全模型参数。
- Qwen3-32B 显存估算按课件题设计算，可从[官方模型配置](https://huggingface.co/Qwen/Qwen3-32B/blob/main/config.json)读取参数。
- [来源说明](materials/sources.md)、[图片鸣谢](materials/images/credits.json)和[中英文术语表](materials/terminology.md)供授课时查阅。
