"""Export a readable session trajectory and compare runs on the same basis."""

import json
from tempfile import NamedTemporaryFile
from collections import Counter
from pathlib import Path


def read_events(path):
    path = Path(path)
    data = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(data)["events"]
    return [json.loads(line) for line in data.splitlines() if line.strip()]


def estimate_tokens(value):
    # A portable size estimate for offline Mock comparisons, not model tokenization.
    return (len(json.dumps(value, ensure_ascii=False).encode("utf-8")) + 3) // 4


def summarize_trajectory(events):
    requests = [event for event in events if event["event"] == "llm_request"]
    responses = {
        event["call_id"]: event["response"]
        for event in events if event["event"] == "llm_response"
    }
    usage = Counter()
    sources = set()
    missing = 0
    for event in requests:
        response = responses.get(event["call_id"])
        if response is None:
            missing += 1
            continue
        recorded = response.get("usage")
        if response.get("teaching_mock"):
            source = "mock_utf8_estimate"
            request = event["request"]
            counts = (
                estimate_tokens({"messages": request["messages"], "tools": request.get("tools", [])}),
                estimate_tokens(response["choices"][0]["message"]),
            )
        else:
            source = "api_usage"
            counts = (recorded.get("prompt_tokens"), recorded.get("completion_tokens")) if isinstance(recorded, dict) else (None, None)
        if any(type(count) is not int or count < 0 for count in counts):
            missing += 1
            continue
        sources.add(source)
        usage.update(dict(zip(("input_tokens", "output_tokens"), counts)))
    status = next((event["status"] for event in reversed(events) if event["event"] == "task_end"), "incomplete")
    comparable = bool(requests) and missing == 0 and len(sources) == 1
    return {
        "status": status,
        "model_calls": len(requests),
        "input_tokens": usage["input_tokens"] if comparable else None,
        "output_tokens": usage["output_tokens"] if comparable else None,
        "token_source": next(iter(sources)) if comparable else None,
        "calls_missing_token_counts": missing,
    }


def default_path(raw_path):
    raw_path = Path(raw_path)
    return raw_path.with_name(f"{raw_path.stem}-session-trajectory.json")


def write_trajectory(raw_path, destination):
    destination = Path(destination)
    events = read_events(raw_path)
    result = {"summary": summarize_trajectory(events), "events": events}
    content = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Publish only after the entire document is written. A named run cannot be overwritten.
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent, delete=False) as file:
        temporary = Path(file.name)
        try:
            file.write(content)
            file.close()
            destination.hardlink_to(temporary)
        finally:
            temporary.unlink()
