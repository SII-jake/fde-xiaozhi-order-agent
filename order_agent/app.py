import argparse, copy, json, logging, time, uuid
from pathlib import Path
from .client import MockClient, APIClient
from .tools import definitions, execute, ORDERS
from .config import load_config, DEFAULT_CONFIG
from .mock_latency import configure as configure_mock_latency
from .trajectory import default_path, write_trajectory
DEFAULT_MODEL = 'Qwen/Qwen3-235B-A22B-Instruct-2507'
DETAILED_REPLY = '请详细说明调查过程、所有核查结果和处理建议。'
logger = logging.getLogger("order_agent")

def configure_logging():
 logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s.%(msecs)03d %(levelname)s %(message)s",
  datefmt="%H:%M:%S",
 )

SYSTEM="你是订单延误调查助手。查询证据与政策，给出当前情况、原因与证据、建议行动及政策依据。不编造事实，不保证预计日期，证据冲突时升级人工。所有操作仅供人工审核。"
class History:
 def __init__(self,path):
  self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
  self.path.touch(exist_ok=False)
 def write(self,event):
  with self.path.open('a') as f: f.write(json.dumps(event,ensure_ascii=False)+'\n')
def run(client,order_id,path,model=DEFAULT_MODEL,max_turns=12,temperature=0,max_tokens=1024,user_message=None,on_tool=None,processing_time=None):
 task_id=str(uuid.uuid4()); history=History(path)
 task_started = time.perf_counter()
 logger.info("task.start session=%s order=%s", task_id[:8], order_id)
 messages=[{'role':'system','content':SYSTEM},{'role':'user','content':user_message or f'订单{order_id}应该昨天到货，现在还没收到。请调查并建议下一步。'}]
 case_time = processing_time or ORDERS[order_id]['as_of'] + ' 09:15'
 time_message = f'当前时间：{case_time}。'
 messages[0]['content'] = time_message + '\n' + SYSTEM
 for step in range(max_turns):
  call_id=str(uuid.uuid4()); started=time.time()
  call_started = time.perf_counter()
  request={'model':model,'messages':copy.deepcopy(messages),'tools':definitions(),'temperature':temperature,'max_tokens':max_tokens}
  if step == 6 and isinstance(client, MockClient):
   request['messages'].append({'role':'user','content':DETAILED_REPLY})
  common={'task_id':task_id,'call_id':call_id,'turn':1,'step_id':call_id,'model_call_index':step+1,'attempt':1}
  history.write({
   **common, 'event': 'llm_request',
   'started_at': started, 'request': request,
  })
  logger.info("llm.start session=%s model_call=%s step=%d", task_id[:8], call_id[:8], step+1)
  try:
   response=client.complete(request)
   choice=response['choices'][0]; message=choice['message']
   elapsed = time.perf_counter() - call_started
   history.write({
    **common, 'event': 'llm_response',
    'finished_at': time.time(), 'elapsed_seconds': elapsed,
    'response': response, 'status': 'ok',
   })
   logger.info("llm.end session=%s model_call=%s step=%d status=ok elapsed_ms=%.3f",
               task_id[:8], call_id[:8], step+1, elapsed*1000)
  except Exception as e:
   logger.exception("llm.error session=%s step=%d", task_id[:8], step+1)
   history.write({**common,'event':'llm_error','elapsed_seconds':time.time()-started,'error':str(e),'status':'error'}); raise
  messages.append(message)
  calls=message.get('tool_calls',[])
  if not calls:
   if choice.get('finish_reason')!='stop':
    history.write({**common,'event':'task_end','status':'incomplete','reason':choice.get('finish_reason')}); raise RuntimeError('Incomplete model response')
   history.write({**common,'event':'task_end','status':'completed'})
   logger.info("task.end session=%s status=completed elapsed_ms=%.3f",
               task_id[:8], (time.perf_counter()-task_started)*1000)
   return message.get('content','')
  for call in calls:
   started=time.time(); function=call['function']; status='ok'
   tool_started = time.perf_counter()
   logger.info("tool.start session=%s model_call=%s step=%s name=%s arguments=%s", task_id[:8], call_id[:8], call['id'], function['name'], function['arguments'])
   try: result=execute(function['name'],json.loads(function['arguments']))
   except Exception as e: result={'error':str(e)}; status='error'
   elapsed = time.perf_counter() - tool_started
   history.write({
    **common, 'event': 'tool_execution', 'step_id': call['id'],
    'tool_call_id': call['id'], 'name': function['name'],
    'arguments': function['arguments'], 'result': result,
    'status': status, 'started_at': started, 'elapsed_seconds': elapsed,
   })
   logger.info("tool.end session=%s model_call=%s step=%s name=%s status=%s elapsed_ms=%.3f result=%s",
               task_id[:8], call_id[:8], call['id'], function['name'], status, elapsed*1000, json.dumps(result,ensure_ascii=False))
   if on_tool is not None:
    on_tool({'name':function['name'], 'arguments':function['arguments'], 'result':result, 'status':status, 'tool_call_id':call['id']})
   messages.append({'role':'tool','tool_call_id':call['id'],'content':result if isinstance(result,str) else json.dumps(result,ensure_ascii=False)})
 history.write({'task_id':task_id,'event':'task_end','status':'turn_limit'}); raise RuntimeError('Maximum model turns reached')
def main():
 configure_logging()
 p=argparse.ArgumentParser(description="小智的订单调查助手")
 p.add_argument('--config',default=str(DEFAULT_CONFIG),help='JSON配置文件')
 p.add_argument('--order',choices=list(ORDERS),default='A1024',help='业务订单编号')
 p.add_argument('--trajectory', type=Path, help='输出会话轨迹 JSON 的路径')
 p.add_argument('--processing-time', help='覆盖案例处理时间，示例 2026-10-30 14:40')
 a=p.parse_args()
 if a.trajectory is not None and a.trajectory.exists():
  p.error(f'轨迹文件已存在：{a.trajectory}')
 config=load_config(a.config); llm=config['llm']
 configure_mock_latency(config['mock'])
 path=Path(config['tracing']['directory'])/(str(uuid.uuid4())+'.jsonl')
 client=MockClient(a.order) if llm['backend']=='mock' else APIClient(llm['base_url'],llm['timeout_seconds'])
 destination = a.trajectory if a.trajectory is not None else default_path(path)
 try:
  print(run(client,a.order,path,llm['model'],config['agent']['max_turns'],llm['temperature'],llm['max_tokens'],processing_time=a.processing_time))
 finally:
  if path.exists():
   write_trajectory(path, destination)
   print('Session trajectory:', destination)
if __name__=='__main__': main()
