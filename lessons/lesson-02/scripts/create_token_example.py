"""Render the downloaded model's actual chat template and tokenize it, no model weights."""
from pathlib import Path
import json,hashlib
from tokenizers import Tokenizer
from jinja2.sandbox import ImmutableSandboxedEnvironment
B=Path(__file__).resolve().parents[1]/'materials';D=B/'tokenizer'
cfg=json.loads((D/'tokenizer_config.json').read_text());tok=Tokenizer.from_file(str(D/'tokenizer.json'))
messages=[{'role':'user','content':'订单A1024在哪？'}]
env=ImmutableSandboxedEnvironment(trim_blocks=True,lstrip_blocks=True)
env.globals['raise_exception']=lambda msg:(_ for _ in ()).throw(ValueError(msg))
rendered=env.from_string(cfg['chat_template']).render(messages=messages,add_generation_prompt=True,tools=None)
enc=tok.encode(rendered,add_special_tokens=False)
rows=[{'index':i,'piece':tok.decode([v],skip_special_tokens=False),'id':v} for i,v in enumerate(enc.ids)]
assert tok.decode(enc.ids,skip_special_tokens=False)==rendered
# Every generated word in the conceptual example is a verified single token.
words=['订单','物流','延误','了','。']
for w in words: assert len(tok.encode(w,add_special_tokens=False).ids)==1,w
assert tok.encode('物流延误了。',add_special_tokens=False).ids == [tok.encode(w,add_special_tokens=False).ids[0] for w in ['物流','延误','了','。']]
result={'model':'Qwen/Qwen3-235B-A22B-Instruct-2507','source':'https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507','messages':messages,'tools':[],'rendered':rendered,'tokens':rows,'count':len(rows),'generated_example':{'text':'物流延误了。','pieces':['物流','延误','了','。'],'ids':[tok.encode(x,add_special_tokens=False).ids[0] for x in ['物流','延误','了','。']],'disclosure':'Scripted illustration, not model-generated output; each piece verified individually.'},'sha256':{f:hashlib.sha256((D/f).read_bytes()).hexdigest() for f in ['tokenizer.json','tokenizer_config.json']}}
(B/'tokenizer-example.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
