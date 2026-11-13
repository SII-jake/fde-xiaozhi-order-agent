"""Calculate per-call and task API costs from the teaching usage in the classroom trace."""

import argparse
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

MILLION = Decimal(1_000_000)
DEFAULT_TRACE = Path(__file__).resolve().parents[2] / "lesson-01/materials/session-history.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, nargs="?", default=DEFAULT_TRACE)
    parser.add_argument("--miss-rate", type=Decimal, default=Decimal("0.30"))
    parser.add_argument("--hit-rate", type=Decimal, default=Decimal("0.006"))
    parser.add_argument("--output-rate", type=Decimal, default=Decimal("1.20"))
    args = parser.parse_args()
    totals = defaultdict(lambda: [Decimal(0), Decimal(0), Decimal(0)])
    trace = json.loads(args.trace.read_text(encoding="utf-8"))
    for row in trace["teaching_usage"]["calls"]:
        task = row["task_id"]
        total_input = int(row["prompt_tokens"])
        hit = int(row["prompt_cache_hit_tokens"])
        miss = int(row["prompt_cache_miss_tokens"])
        output = int(row["completion_tokens"])
        if min(total_input, hit, miss, output) < 0 or hit + miss != total_input:
            raise ValueError(f"{task} 第 {row['turn']} 次调用的用量无效")
        output_cost = output * args.output_rate
        charged = (hit * args.hit_rate + miss * args.miss_rate + output_cost) / MILLION
        totals[task][0] += charged
        totals[task][1] += (total_input * args.hit_rate + output_cost) / MILLION
        totals[task][2] += (total_input * args.miss_rate + output_cost) / MILLION
        print(f"{task} 第 {row['turn']} 次：${charged:.9f}")
    for task, (charged, all_hit, all_miss) in totals.items():
        print(f"{task} 汇总：${charged:.9f}，全命中 ${all_hit:.9f}，全未命中 ${all_miss:.9f}")


if __name__ == "__main__":
    main()
