"""Check deterministic results from the classroom optimization fixtures."""
import json
from decimal import Decimal
from pathlib import Path

MATERIALS = Path(__file__).resolve().parents[1] / "materials"


def common_prefix_length(first, second):
    for index, (left, right) in enumerate(zip(first, second)):
        if left != right:
            return index
    return min(len(first), len(second))


def policy_for_model(result):
    return {key: value for key, value in result.items() if key != "front_matter"}


def route(label):
    return "低成本模型" if label in {"delivery", "refund", "account"} else "强模型复判"


def input_fee(hit, miss):
    return (hit * Decimal("0.006") + miss * Decimal("0.30")) / 1_000_000


def main():
    replay = json.loads((MATERIALS / "a1024-multi-tool-inputs.json").read_text())
    policy = json.loads((MATERIALS / "policy-document-front-matter.json").read_text())
    routing = json.loads((MATERIALS / "routing-example.json").read_text())
    messages = json.loads((MATERIALS / "multi-tool-message.json").read_text())
    projected = policy_for_model(policy)
    assert "front_matter" in policy and "front_matter" not in projected
    rows = replay["rows"]
    before = sum(row["offline_input_tokens"] for row in rows)
    after = sum(row["without_front_matter"] for row in rows)
    calls = [call["function"]["name"] for call in messages["message"]["tool_calls"]]
    assert calls == ["get_order", "get_warehouse_events"]
    assert (before, after) == (10040, 9630)
    print(f"方法 1：{calls}，六次模型调用回放")
    print(f"方法 4：原始政策完整，模型输入去除前置页；{before} → {after}")
    print("方法 6：用同一分词器获得两组 token ID，再传给 common_prefix_length")
    print("方法 7：以下路由由教学模型响应决定")
    for example in routing:
        print(f"  {example['message']} → {route(example['mock_low_model'])}")
    print(f"方法 8：保留工具且命中 1728 时 ${input_fee(1728, 106):.9f}")
    print(f"        清空工具且全未命中时 ${input_fee(0, 603):.9f}")


if __name__ == "__main__":
    main()
