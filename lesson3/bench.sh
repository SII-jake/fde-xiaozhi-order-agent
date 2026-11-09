#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ ]]; then
    echo "用法：bash lesson3/bench.sh <本次记录名称>，例如 baseline" >&2
    exit 2
fi

lab_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
result_name="$1.json"
result_dir="$lab_dir/results"
if [[ -e "$result_dir/$result_name" ]]; then
    echo "记录已存在，请换一个名称：$result_dir/$result_name" >&2
    exit 2
fi
mkdir -p -- "$result_dir"

vllm bench serve \
    --backend openai-chat \
    --base-url "${LAB_BASE_URL:-http://127.0.0.1:8000}" \
    --endpoint /v1/chat/completions \
    --model "${LAB_MODEL:-Qwen/Qwen3-0.6B}" \
    --served-model-name order-demo-0.6b \
    --dataset-name custom --dataset-path "$lab_dir/requests.jsonl" \
    --num-prompts 20 --custom-output-len 32 \
    --max-concurrency 4 --request-rate inf --seed 42 --num-warmups 1 \
    --metric-percentiles 95 --percentile-metrics ttft,itl,e2el \
    --extra-body '{"chat_template_kwargs":{"enable_thinking":false}}' \
    --save-result --result-dir "$result_dir" --result-filename "$result_name"

printf '\n报告文件：%s\n' "$result_dir/$result_name"
