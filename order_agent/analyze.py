"""Analyze per-call contexts without inventing token attribution."""
import argparse,json
from pathlib import Path
def summarize(path):
 events=[json.loads(x) for x in Path(path).read_text().splitlines()]
 rows=[]
 for e in events:
  if e['event']!='llm_request': continue
  req=e['request']; counts={}
  for m in req['messages']:
   role=m['role']; counts[role]=counts.get(role,0)+len(json.dumps(m,ensure_ascii=False))
  counts['tool_definitions']=len(json.dumps(req.get('tools',[]),ensure_ascii=False))
  response=next((x for x in events if x['event']=='llm_response' and x['call_id']==e['call_id']),None)
  rows.append({'turn':e['turn'],'context_serialized_characters':counts,'usage':response['response'].get('usage') if response else None,'seconds':response.get('elapsed_seconds') if response else None})
 return {'note':'字符数用于内容观察，不是token数或GPU费用。mock不提供真实usage；工具历史仍可按工具调用ID追溯来源。','calls':rows}
def main():
 p=argparse.ArgumentParser();p.add_argument('trace');a=p.parse_args();print(json.dumps(summarize(a.trace),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
