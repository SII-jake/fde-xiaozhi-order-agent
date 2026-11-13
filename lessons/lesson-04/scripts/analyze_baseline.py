from pathlib import Path
import json,csv
from tokenizers import Tokenizer
from jinja2.sandbox import ImmutableSandboxedEnvironment
R=Path(__file__).resolve().parents[3];D=R/'lessons/lesson-02/materials/tokenizer';tok=Tokenizer.from_file(str(D/'tokenizer.json'));cfg=json.loads((D/'tokenizer_config.json').read_text());env=ImmutableSandboxedEnvironment(trim_blocks=True,lstrip_blocks=True);tpl=env.from_string(cfg['chat_template']);rows=[]
for line in (R/'lessons/lesson-01/materials/session-history.jsonl').read_text().splitlines():
 e=json.loads(line)
 if e.get('event')!='llm_request':continue
 q=e['request'];txt=tpl.render(messages=q['messages'],tools=q.get('tools'),add_generation_prompt=True)
 counts={r:sum(len(m.get('content') or '') for m in q['messages'] if m['role']==r) for r in ['system','user','assistant','tool']}
 rows.append({'turn':e['turn'],'call_id':e['call_id'],'offline_input_tokens':len(tok.encode(txt,add_special_tokens=False).ids),'tool_definition_count':len(q.get('tools',[])),'system_chars':counts['system'],'user_chars':counts['user'],'assistant_content_chars':counts['assistant'],'tool_result_chars':counts['tool'],'api_usage':None})
meta={'disclosure':'Offline re-tokenization of lesson1 mock requests; not API usage, GPU measurement, billing or representative traffic. Jinja serialization may differ from serving runtime.','model':'Qwen/Qwen3-235B-A22B-Instruct-2507','character_fields_note':'Character columns are content-only, not token attribution. Full rendered input token count includes tool-call names, arguments and schemas.','rows':rows}
(R/'lessons/lesson-04/materials/baseline-context-analysis.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
with (R/'lessons/lesson-04/materials/baseline-context-analysis.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps(rows,ensure_ascii=False))
