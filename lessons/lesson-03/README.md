# 课 3：推理引擎部署与优化

[练习输入与参考答案](materials/exercises.md)

[讲师脚本](lesson-03-script.md)与[第 38 版课件](pptx/output/lesson-03-v38.pptx)共 47 页，建议 90 分钟。

P01–P07 从模型文件讲到推理引擎和 CPU 部署，中间用 P03 的五层部署图串起订单、模型副本、Transformer 层、层内模块和 GPU。P08–P14 讲容量余量，先带读八卡模拟报告，再让学员实测并分析 CPU 基线。P15 引入两个优化方向。P16–P27 讲减少闲置（调度与模型副本分流），P28–P43 讲减少每单资源使用，其中 P34–P36 专讲缓存亲和性调度。P44–P45 是速查表，P46 完成 CPU 调参练习，P47 衔接课 4。

- [学员手册](materials/vllm-deployment-lab.docx)
- [学员项目的测量工具](../../lesson3/bench.sh)与[固定请求集](../../lesson3/requests.jsonl)，在项目的 `lesson3/` 目录
- [CPU 起始配置](../../lesson3/serve-demo.yaml)、[八卡案例配置](materials/serve-case.yaml)
- [环境准备](materials/environment-record.md)
- [普通请求](materials/smoke-request.json)、[工具调用请求](materials/tool-request.json)
- [测量记录空表](materials/experiment-record.csv)
- [A1026 调查记录摘录](materials/a1026-investigation-input.html)
- [调优备课笔记](materials/vllm-teaching-notes.md)

四章导航依次为「服务部署、性能测量、部署优化、复测与交接」。课堂实测 CPU 服务。小智案例的高峰流量、容量和延迟是教学模拟。开课前请在教学机试跑基线与候选配置。
