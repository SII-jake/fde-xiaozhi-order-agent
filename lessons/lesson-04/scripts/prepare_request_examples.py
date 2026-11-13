"""Extract concrete requests for methods 5, 6, and 8 from the classroom replay."""

import copy
import json
from pathlib import Path

MATERIALS = Path(__file__).resolve().parents[1] / "materials"


def timed_pair(request, placement):
    pair = []
    for timestamp in ("09:15:01", "09:15:02"):
        candidate = copy.deepcopy(request)
        if placement == "system":
            system = candidate["messages"][0]
            system["content"] = f"当前时间 {timestamp}。{system['content']}"
        else:
            user = next(m for m in candidate["messages"] if m["role"] == "user")
            user["content"] += f" 本次处理时间为 {timestamp}。"
        pair.append(candidate)
    return pair


def main():
    lines = (MATERIALS / "a1024-filtered.jsonl").read_text(encoding="utf-8").splitlines()
    requests = [e["request"] for e in map(json.loads, lines) if e["event"] == "llm_request"]
    previous, final = requests[-2:]
    concise = copy.deepcopy(final)
    concise["messages"][0]["content"] += (
        "证据齐备后，按结论与证据、预计时间、下一步、政策依据四项答复，每项最多一句。"
    )
    no_tools = {**final, "tools": []}
    print(json.dumps({
        "provenance": "从六次 Mock 回放复制请求，供离线比较或实际模型复测",
        "method_5": {"baseline": final, "concise_instruction": concise},
        "method_6": {"time_at_system_start": timed_pair(final, "system"),
                     "time_in_order_context": timed_pair(final, "user")},
        "method_8": {"previous_request": previous, "full_tools": final, "no_tools": no_tools},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
