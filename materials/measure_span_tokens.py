"""Compare execution spans and offline Qwen token counts for the lesson 4 demo."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from jinja2.sandbox import ImmutableSandboxedEnvironment
from tokenizers import Tokenizer

from order_agent.app import run
from order_agent.client import MockClient
from order_agent.config import load_config
from order_agent.tools import ORDERS

ROOT = Path(__file__).resolve().parents[1]
TOKENIZER_DIR = ROOT / "materials"


def measure(order, trace, config, encode):
    optimization = config["agent"].get("optimization")
    run(
        MockClient(order, optimized=bool(optimization)),
        order,
        trace,
        model=config["llm"]["model"],
        optimization=optimization,
    )
    events = [json.loads(line) for line in trace.read_text().splitlines()]
    requests = [event["request"] for event in events if event["event"] == "llm_request"]
    responses = [
        event["response"]["choices"][0]["message"]
        for event in events
        if event["event"] == "llm_response"
    ]
    tools = sum(event["event"] == "tool_execution" for event in events)
    # The application records the order and optional tracking lookup in one event.
    tools += sum(
        1 + int(event["result"]["tracking"] is not None)
        for event in events
        if event["event"] == "application_prefetch"
    )
    assistant_header = len(encode([{"role": "assistant", "content": ""}])) - 2
    return {
        "span_count": len(requests) + tools,
        "model_calls": len(requests),
        "tool_calls": tools,
        "input_tokens": sum(
            len(encode(request["messages"], request["tools"], generation_prompt=True))
            for request in requests
        ),
        "output_tokens": sum(len(encode([response])) - assistant_header for response in responses),
    }


def main():
    tokenizer = Tokenizer.from_file(str(TOKENIZER_DIR / "tokenizer.json"))
    config = json.loads((TOKENIZER_DIR / "tokenizer_config.json").read_text())
    environment = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)
    template = environment.from_string(config["chat_template"])

    def encode(messages, tools=None, generation_prompt=False):
        rendered = template.render(
            messages=messages, tools=tools, add_generation_prompt=generation_prompt
        )
        return tokenizer.encode(rendered, add_special_tokens=False).ids

    configs = {
        name: load_config(ROOT / "config" / filename)
        for name, filename in (("baseline", "local.json"), ("optimized", "optimized.json"))
    }
    with TemporaryDirectory() as directory, patch("order_agent.mock_latency.time.sleep"):
        results = {
            order: {
                name: measure(order, Path(directory) / f"{order}-{name}.jsonl", cfg, encode)
                for name, cfg in configs.items()
            }
            for order in ORDERS
        }
    print(json.dumps({
        "measurement": "同一 Qwen 聊天模板与分词器离线复算，输出包含工具调用和消息结束标记。两版都按同一 Qwen 分词口径统计，不折算模型价格，数值不等同于 API usage。",
        "orders": results,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
