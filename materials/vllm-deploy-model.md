# 使用vllm部署一个qwen3\-0\.6B模型

## 登陆后端服务器

使用分配给你的 SSH 账号登录服务器。

conda/docker/vllm已预装



## 部署模型

命令1: 下载模型

```Plain Text
modelscope download --model Qwen/Qwen3-0.6B --local_dir ~/workspace/Qwen3-0.6B
```



命令2: 进入到vllm容器

```Plain Text
docker run --ipc=host -it \
  -v ~/workspace/Qwen3-0.6B:/vllm-workspace/Qwen3-0.6B \
  -e VLLM_USE_MODELSCOPE=True \
  --entrypoint /bin/bash \
  -p 8000:8000 \
  vllm-openai-cpu-local:latest
```



命令3: 启动vllm推理服务

启动脚本

```Bash
#!/bin/bash

#VLLM的环境变量
export VLLM_CPU_KVCACHE_SPACE=1

#启动命令
python -m vllm.entrypoints.openai.api_server \
  --model Qwen3-0.6B \
  --max-model-len 8192 \
  --trust-remote-code
```



更多参数见：https://vllm\.hyper\.ai/docs/inference\-and\-serving/engine\_args/





## 测试推理服务

输入以下命令测试：

```C++
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3-0.6B",
    "messages": [
      {"role": "user", "content": "我想去北京旅游，有什么推荐的景点吗？"},
      {"role": "assistant", "content": "北京有很多著名景点，比如故宫、天安门、长城等。"},
      {"role": "user", "content": "能详细介绍一下长城吗？"}
    ],
    "max_tokens": 150,
    "temperature": 0.7
  }'
```



```C++
curl http://${公网IP}:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3-0.6B",
    "messages": [
      {"role": "user", "content": "我想去北京旅游，有什么推荐的景点吗？"},
      {"role": "assistant", "content": "北京有很多著名景点，比如故宫、天安门、长城等。"},
      {"role": "user", "content": "能详细介绍一下长城吗？"}
    ],
    "max_tokens": 150,
    "temperature": 0.7
  }'
```
