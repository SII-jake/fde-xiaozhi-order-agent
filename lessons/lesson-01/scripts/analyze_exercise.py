"""Read the classroom trace and summarize its annotated teaching usage."""
import argparse
import json
from pathlib import Path

LESSONS = Path(__file__).resolve().parents[2]

def analyze(trace_path):
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    events = trace["events"]
    models = [event for event in events if event["event"] == "llm_response"]
    tools = [event for event in events if event["event"] == "tool_execution"]
    usage = trace["teaching_usage"]["calls"]
    if [int(row["turn"]) for row in usage] != [event["turn"] for event in models]:
        raise ValueError("用量数据与模型调用序号不一致")
    keys = ("prompt_cache_miss_tokens", "prompt_cache_hit_tokens", "prompt_tokens", "completion_tokens")
    totals = {key: sum(int(row[key]) for row in usage) for key in keys}
    if totals["prompt_tokens"] != totals["prompt_cache_miss_tokens"] + totals["prompt_cache_hit_tokens"]:
        raise ValueError("输入分类与总量不一致")
    return {
        "model_calls": len(models),
        "tool_calls": len(tools),
        "mock_usage_missing": sum(event["response"].get("usage") is None for event in models),
        "tool_sequence": [
            {"model_call": tool["turn"], "tool": tool["name"], "arguments": json.loads(tool["arguments"])}
            for tool in tools
        ],
        "teaching_usage": totals,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, default=LESSONS / "lesson-01/materials/session-history.json")
    args = parser.parse_args()
    print(json.dumps(analyze(args.trace), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
