import argparse, copy, json, time, uuid
from pathlib import Path
from .client import MockClient, APIClient
from .tools import definitions, execute, ORDERS
SYSTEM="你是订单延误调查助手。查询证据与政策，给出当前情况、原因与证据、建议行动及政策依据。不编造事实，不保证预计日期，证据冲突时升级人工。所有操作仅供人工审核。"
class History:
 def __init__(self,path):
  self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
  self.path.touch(exist_ok=False)
 def write(self,event):
  with self.path.open('a') as f: f.write(json.dumps(event,ensure_ascii=False)+'\n')
def run(client,order_id,path,model='teaching-mock',max_turns=12):
 task_id=str(uuid.uuid4()); history=History(path)
 messages=[{'role':'system','content':SYSTEM},{'role':'user','content':f'订单{order_id}应该昨天到货，现在还没收到。请调查并建议下一步。'}]
 for turn in range(max_turns):
  call_id=str(uuid.uuid4()); started=time.time()
  request={'model':model,'messages':copy.deepcopy(messages),'tools':definitions(),'temperature':0,'max_tokens':1024}
  common={'task_id':task_id,'call_id':call_id,'turn':turn+1,'attempt':1}
  history.write({**common,'event':'llm_request','started_at':started,'request':request})
  try:
   response=client.complete(request)
   choice=response['choices'][0]; message=choice['message']
   history.write({**common,'event':'llm_response','finished_at':time.time(),'elapsed_seconds':time.time()-started,'response':response,'status':'ok'})
  except Exception as e:
   history.write({**common,'event':'llm_error','elapsed_seconds':time.time()-started,'error':str(e),'status':'error'}); raise
  messages.append(message)
  calls=message.get('tool_calls',[])
  if not calls:
   if choice.get('finish_reason')!='stop':
    history.write({**common,'event':'task_end','status':'incomplete','reason':choice.get('finish_reason')}); raise RuntimeError('Incomplete model response')
   history.write({**common,'event':'task_end','status':'completed'}); return message.get('content','')
  for call in calls:
   started=time.time(); function=call['function']; status='ok'
   try: result=execute(function['name'],json.loads(function['arguments']))
   except Exception as e: result={'error':str(e)}; status='error'
   history.write({**common,'event':'tool_execution','tool_call_id':call['id'],'name':function['name'],'arguments':function['arguments'],'result':result,'status':status,'started_at':started,'elapsed_seconds':time.time()-started})
   messages.append({'role':'tool','tool_call_id':call['id'],'content':json.dumps(result,ensure_ascii=False)})
 history.write({'task_id':task_id,'event':'task_end','status':'turn_limit'}); raise RuntimeError('Maximum model turns reached')
def main():
 p=argparse.ArgumentParser(); p.add_argument('--backend',choices=['mock','api'],default='mock'); p.add_argument('--order',choices=list(ORDERS),default='A1024'); p.add_argument('--base-url',default='http://localhost:8000/v1'); p.add_argument('--model',default='Qwen/Qwen3-235B-A22B-Instruct-2507'); p.add_argument('--trace',default='traces/'+str(uuid.uuid4())+'.jsonl'); a=p.parse_args()
 client=MockClient(a.order) if a.backend=='mock' else APIClient(a.base_url)
 print(run(client,a.order,a.trace,'teaching-mock' if a.backend=='mock' else a.model)); print('Conversation history:',a.trace)
if __name__=='__main__': main()
