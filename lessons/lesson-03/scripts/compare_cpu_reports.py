"""Compare classroom vLLM benchmark reports."""
import argparse
import json
from pathlib import Path

METRICS = {
    "request_throughput": "请求吞吐（条/秒）",
    "p95_ttft_ms": "P95 首 token（ms）",
    "p95_itl_ms": "P95 后续间隔（ms）",
    "p95_e2el_ms": "P95 端到端（ms）",
}

def read_report(path, request_count):
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("num_prompts", request_count) != request_count or not 0 <= report["completed"] <= request_count:
        raise ValueError(f"{path} 的样本数与完成数不匹配")
    return {"成功率（%）": 100 * report["completed"] / request_count,
            **{label: report[key] for key, label in METRICS.items()}}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--request-count", type=int, default=20)
    args = parser.parse_args()
    if args.request_count <= 0:
        parser.error("请求数必须大于 0")
    before = read_report(args.baseline, args.request_count)
    after = read_report(args.candidate, args.request_count)
    for name, value in before.items():
        print(f"{name}：{value:.3f} → {after[name]:.3f}（变化 {after[name] - value:+.3f}）")

if __name__ == "__main__":
    main()
