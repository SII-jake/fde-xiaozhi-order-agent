"""Reproduce teaching estimates; no GPU access or performance claims."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / 'materials/model-config-excerpt.json').read_text())
c = source['config_excerpt']
a = source['course_assumptions']
GIB = 2**30
weight = a['total_parameters_rounded'] * a['weight_bytes_per_parameter']
nominal = a['gpus_per_replica'] * a['gpu_nominal_gb'] * 10**9
per_token = 2 * c['num_hidden_layers'] * c['num_key_value_heads'] * c['head_dim'] * a['kv_bytes_per_element']
# Conditional deployment example: each TP rank stores at least one KV head.
# Not a claim that all engines/backends use this layout.
tp = a['gpus_per_replica']
assert tp % c['num_key_value_heads'] == 0
local_kv_heads = max(1, c['num_key_value_heads'] // tp)
local_per_token = 2 * c['num_hidden_layers'] * local_kv_heads * c['head_dim'] * a['kv_bytes_per_element']
rows = []
for tokens in (8192, 32768):
    for sequences in (1, 4):
        logical = per_token * tokens * sequences
        conditional_per_gpu = local_per_token * tokens * sequences
        rows.append({
            'cached_tokens_per_sequence': tokens,
            'active_sequences': sequences,
            'logical_kv_gib': logical / GIB,
            'conditional_tp8_kv_gib_per_gpu': conditional_per_gpu / GIB,
            'conditional_tp8_kv_gib_all_gpus': conditional_per_gpu * tp / GIB,
        })
result = {
    'kind': 'physical-size estimates, not measured capacity or performance',
    'units': {'GB': '10^9 bytes', 'GiB': '2^30 bytes', 'KiB': '2^10 bytes'},
    'weight_bytes': weight,
    'weight_gb': weight / 10**9,
    'weight_gib': weight / GIB,
    'nominal_replica_capacity_gb': nominal / 10**9,
    'nominal_difference_before_runtime_and_kv_gb': (nominal - weight) / 10**9,
    'logical_kv_bytes_per_token': per_token,
    'logical_kv_kib_per_token': per_token / 1024,
    'conditional_tp8_kv_replication_factor': local_per_token * tp / per_token,
    'examples': rows,
    'excluded': ['runtime buffers', 'activations', 'graph pools', 'page rounding', 'engine overhead', 'other processes', 'latency and quality requirements'],
    'limitations': [
        'Rounded model parameter count; nominal GPU capacity is not observed allocatable memory.',
        'KV assumes BF16, no cross-request sharing, no sliding window, equal cached lengths in each example.',
        'TP8 figures assume KV-head replication with at least one head per rank. Verify the selected engine version/backend.',
        'No maximum concurrency, tokens/s, or releasable server count is inferred.'
    ]
}
out = ROOT / 'materials/memory-budget.json'
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(f'Wrote {out.name}: weight={result["weight_gb"]:.0f} GB; logical KV={per_token/1024:.0f} KiB/token')
