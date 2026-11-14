import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
import os
from pathlib import Path
from time import perf_counter
from urllib.error import URLError
from urllib.request import Request, urlopen

MATERIALS = Path(__file__).resolve().parent
DEFAULT_CONFIG = MATERIALS.parent / "config/bench.json"


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("必须大于 0")
    return number


def p95(values):
    if not values:
        return None
    return round(sorted(values)[math.ceil(0.95 * len(values)) - 1] * 1000, 3)


def measure(prompt, args):
    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": args.max_tokens,
        "stream": True,
    }
    if args.disable_thinking:
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
    if key := os.getenv("LLM_API_KEY"):
        headers["Authorization"] = "Bearer " + key
    request = Request(
        args.base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
    )
    started = perf_counter()
    chunks = []
    finished = False
    try:
        with urlopen(request, timeout=args.timeout) as response:
            for raw in response:
                if not raw.startswith(b"data:"):
                    continue
                data = raw[5:].strip()
                if data == b"[DONE]":
                    finished = True
                    break
                event = json.loads(data)
                if event.get("error"):
                    raise ValueError("服务返回流式错误")
                for choice in event.get("choices", []):
                    delta = choice.get("delta") or {}
                    if delta.get("content"):
                        chunks.append(perf_counter())
                    if choice.get("finish_reason"):
                        finished = True
        if not finished or not chunks:
            raise ValueError("未收到完整的可见文本响应")
        return chunks[0] - started, perf_counter() - started, [
            later - earlier for earlier, later in zip(chunks, chunks[1:])
        ], None
    except (OSError, URLError, ValueError) as exc:
        return None, None, [], str(exc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", nargs="?", default="baseline", help="报告名称，默认 baseline")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="测试目标配置文件")
    parser.add_argument("--base-url", help="覆盖配置中的接口地址，包含 /v1")
    parser.add_argument("--model", help="覆盖配置中的 API 模型名")
    parser.add_argument("--dataset", type=Path, default=MATERIALS / "requests.jsonl")
    parser.add_argument("--concurrency", type=positive_int, default=4)
    parser.add_argument("--max-tokens", type=positive_int, default=32)
    parser.add_argument("--timeout", type=positive_int, default=120)
    parser.add_argument("--disable-thinking", action="store_true",
                        help="仅在支持 chat_template_kwargs 的 Qwen 服务上使用")
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        args.base_url = args.base_url or os.getenv("LAB_BASE_URL") or config["base_url"]
        args.model = args.model or os.getenv("LAB_MODEL") or config["model"]
        if not isinstance(args.base_url, str) or not args.base_url.startswith(("http://", "https://")):
            raise ValueError("base_url 必须为 HTTP(S) 接口地址")
        if not isinstance(args.model, str) or not args.model.strip():
            raise ValueError("model 必须为服务端 API 接受的模型名")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.error(f"配置读取失败（{args.config}）：{exc}")
    if not args.name.isascii() or not args.name.replace("-", "").replace("_", "").isalnum():
        parser.error("报告名称只能使用英文字母、数字、下划线和连字符")
    destination = MATERIALS / "results" / f"{args.name}.json"
    if destination.exists():
        parser.error(f"报告已存在：{destination}")
    try:
        prompts = [
            json.loads(line)["prompt"]
            for line in args.dataset.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if not prompts or any(not isinstance(p, str) or not p.strip() for p in prompts):
            raise ValueError("请求集需要至少一条非空 prompt")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))

    warmup = measure(prompts[0], args)
    if warmup[3] is not None:
        parser.exit(1, f"预热请求失败：{warmup[3]}\n")
    started = perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        results = list(pool.map(lambda prompt: measure(prompt, args), prompts))
    elapsed = perf_counter() - started
    completed = [result for result in results if result[3] is None]
    report = {
        "model": args.model,
        "num_prompts": len(prompts),
        "completed": len(completed),
        "failed": len(prompts) - len(completed),
        "success_rate": len(completed) / len(prompts),
        "concurrency": args.concurrency,
        "max_tokens": args.max_tokens,
        "duration_seconds": round(elapsed, 3),
        "request_throughput": round(len(completed) / elapsed, 3),
        "p95_ttft_ms": p95([r[0] for r in completed]),
        "p95_chunk_gap_ms": p95([gap for r in completed for gap in r[2]]),
        "p95_e2el_ms": p95([r[1] for r in completed]),
        "errors": {str(i): r[3] for i, r in enumerate(results, 1) if r[3]},
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8") as file:
            json.dump(report, file, ensure_ascii=False, indent=2)
            file.write("\n")
    except FileExistsError:
        parser.error(f"报告已存在：{destination}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"报告文件：{destination}")


if __name__ == "__main__":
    main()
