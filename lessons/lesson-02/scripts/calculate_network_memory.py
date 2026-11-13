"""BF16 weight-size breakdown from the official model configuration.
No model weights or GPU are loaded; activations are illustrative tensor sizes.
"""
import json
from pathlib import Path
r = Path(__file__).resolve().parents[1]
c = json.loads((r/'materials/model-config-excerpt.json').read_text())['config_excerpt']
h, d, q, kv, layers = c['hidden_size'], c['head_dim'], c['num_attention_heads'], c['num_key_value_heads'], c['num_hidden_layers']
parts = {
 'embedding': c['vocab_size'] * h * 2,
 'attention_per_layer': (h*q*d + 2*h*kv*d + q*d*h)*2,
 'experts_per_layer': 3*h*c['moe_intermediate_size']*c['num_experts']*2,
 'router_per_layer': h*c['num_experts']*2,
 'norms_per_layer': (2*h+2*d)*2,
 'final_norm': h*2,
 'output_head': c['vocab_size']*h*2,
}
total = parts['embedding'] + layers*sum(parts[k] for k in ('attention_per_layer','experts_per_layer','router_per_layer','norms_per_layer')) + parts['final_norm'] + parts['output_head']
assert total == 470187269120  # official safetensors index metadata.total_size
result = {'source_config':'https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507/raw/main/config.json', 'source_index':'https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507/raw/main/model.safetensors.index.json', 'checked_on':'2026-11-04','basis':'BF16 raw tensor sizes calculated from shapes; matches official index total_size; not measured allocated GPU memory','parts_bytes':parts,'total_weight_bytes':total,'total_weight_gb':total/10**9,'layers':layers,'illustrative_hidden_tensor':{'formula':'tokens * hidden_size * 2 bytes','tokens':32768,'bytes':32768*h*2,'mib':32768*h*2/2**20},'excludes':['KV','attention/FFN intermediates','communication and execution buffers','allocator overhead','TP replication']}
(r/'materials/network-memory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('BF16 raw weights:',total/10**9,'GB; one 32K hidden tensor:',256,'MiB')

parameters = {"basis": "Parameter counts derived from tensor shapes", "source_config": result["source_config"], "source_index": result["source_index"], "parts_parameters": {k: v // 2 for k, v in parts.items()}, "layers": layers, "total_parameters": total // 2}
(r/"materials/network-parameters.json").write_text(json.dumps(parameters, ensure_ascii=False, indent=2)+"\n")
