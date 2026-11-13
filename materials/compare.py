"""Run both lesson 4 variants against the same three mock orders."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from order_agent.app import run
from order_agent.client import MockClient
from order_agent.config import load_config
from order_agent.tools import ORDERS

ROOT = Path(__file__).resolve().parents[1]


def measure(order, config, path):
    optimization = config["agent"].get("optimization")
    answer = run(
        MockClient(order, optimized=bool(optimization)), order, path, model=config["llm"]["model"],
        optimization=optimization,
    )
    events = [json.loads(line) for line in path.read_text().splitlines()]
    requests = [e["request"] for e in events if e["event"] == "llm_request"]
    return {
        "model_calls": len(requests),
        "request_chars": sum(
            len(json.dumps({k: request[k] for k in ("messages", "tools")}, ensure_ascii=False))
            for request in requests
        ),
        "answer_chars": len(answer),
        "first_tool_names": [
            e["name"] for e in events if e["event"] == "tool_execution" and e["turn"] == 1
        ],
        "prefetched": any(e["event"] == "application_prefetch" for e in events),
        "final_tools": len(requests[-1]["tools"]),
        "final_model": requests[-1]["model"],
        "answer": answer,
    }


def main():
    configs = {name: load_config(ROOT / "config" / file) for name, file in
               (("baseline", "local.json"), ("optimized", "optimized.json"))}
    configs["baseline"]["llm"]["model"] = configs["optimized"]["llm"]["model"]
    with tempfile.TemporaryDirectory() as directory, patch("order_agent.mock_latency.time.sleep"):
        results = {
            order: {
                name: measure(order, config, Path(directory) / f"{order}-{name}.jsonl")
                for name, config in configs.items()
            }
            for order in ORDERS
        }
    print(json.dumps({
        "measurement": "Mock 运行。输入字符只统计 messages 与 tools。费用、缓存命中和真实模型质量待实测。",
        "orders": results,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
