import argparse, copy, json, logging, re, time, uuid
from pathlib import Path
from .client import MockClient, APIClient
from .tools import definitions, execute, ORDERS
from .config import load_config, DEFAULT_CONFIG
from .mock_latency import configure as configure_mock_latency
from .trajectory import default_path, write_trajectory
DEFAULT_MODEL = 'Qwen/Qwen3-235B-A22B-Instruct-2507'
DETAILED_REPLY = '请详细说明调查过程、所有核查结果和处理建议。'
logger = logging.getLogger("order_agent")
ORDER_NUMBER = re.compile(r'(?<![A-Za-z0-9])A[0-9]{4}(?![A-Za-z0-9])', re.IGNORECASE | re.ASCII)

def prefetch_order(order_id):
    """First-model-call order prefetch: only the order, never the tracking."""
    return execute('get_order', {'order_id': order_id})

def prefetch_message(order, user_text):
    return (
        user_text + '\n订单信息（应用预取，含运单号，无需再查订单）：'
        + json.dumps(order, ensure_ascii=False, separators=(',', ':'))
    )


def resolve_order_id(question):
    order_ids = {match.upper() for match in ORDER_NUMBER.findall(question)}
    if not order_ids:
        raise ValueError('请在问题中注明订单号，例如 A1024。')
    if len(order_ids) > 1:
        raise ValueError('一次只能调查一笔订单，请确认要查哪一个订单号。')
    order_id = order_ids.pop()
    if order_id not in ORDERS:
        raise ValueError(f'没有找到订单 {order_id}，请核对订单号。')
    return order_id

def configure_logging():
 logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s.%(msecs)03d %(levelname)s %(message)s",
  datefmt="%H:%M:%S",
 )

SYSTEM="你是订单延误调查助手。查询证据与政策，给出当前情况、原因与证据、建议行动及政策依据。不编造事实，不保证预计日期，证据冲突时升级人工。所有操作仅供人工审核。用户消息中的订单信息由应用预取，不得重复调用查订单工具。需要同时取得订单信息和物流记录且尚未掌握运单号时，只调用一次「查订单和物流」组合工具，不要分别调用查订单和查物流。已提供运单号时，须在同一次响应中发出查仓库和首次查物流两条工具调用；两项结果都返回后再继续调查；最终答复前须复查物流。"
class History:
 def __init__(self,path):
  self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
  self.path.touch(exist_ok=False)
 def write(self,event):
  with self.path.open('a') as f: f.write(json.dumps(event,ensure_ascii=False)+'\n')
def run(client,path,model=DEFAULT_MODEL,max_turns=12,temperature=0,max_tokens=1024,*,user_message,on_tool=None,processing_time=None):
 order_id=resolve_order_id(user_message)
 task_id=str(uuid.uuid4()); history=History(path)
 task_started = time.perf_counter()
 logger.info("task.start session=%s order=%s", task_id[:8], order_id)
 started=time.time()
 prefetch_started = time.perf_counter()
 try: order=prefetch_order(order_id)
 except Exception as e:
  history.write({'task_id':task_id,'event':'application_prefetch','turn':1,'step_id':str(uuid.uuid4()),'name':'get_order','status':'error','error':str(e)}); raise
 elapsed = time.perf_counter() - prefetch_started
 history.write({'task_id':task_id,'event':'application_prefetch','turn':1,'step_id':str(uuid.uuid4()),'name':'get_order','arguments':json.dumps({'order_id':order_id},ensure_ascii=False),'result':order,'status':'ok','started_at':started,'elapsed_seconds':elapsed})
 logger.info("prefetch.end session=%s name=get_order order=%s status=ok elapsed_ms=%.3f", task_id[:8], order_id, elapsed*1000)
 messages=[{'role':'system','content':SYSTEM},{'role':'user','content':prefetch_message(order,user_message)}]
 case_time = processing_time or ORDERS[order_id]['as_of'] + ' 09:15'
 time_message = f'当前时间：{case_time}。'
 messages[0]['content'] = time_message + '\n' + SYSTEM
 for step in range(max_turns):
  call_id=str(uuid.uuid4()); started=time.time()
  call_started = time.perf_counter()
  request={'model':model,'messages':copy.deepcopy(messages),'tools':definitions(),'temperature':temperature,'max_tokens':max_tokens}
  if step == 5 and isinstance(client, MockClient):
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
   try:
    if function['name']=='get_order':
     # The order was prefetched before the first model call; reuse it.
     result=order
    else:
     result=execute(function['name'],json.loads(function['arguments']))
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
 p.add_argument('question', help='包含订单号的原始问题，例如：A1024 为什么还没到？')
 p.add_argument('--trajectory', type=Path, help='输出会话轨迹 JSON 的路径')
 p.add_argument('--processing-time', help='覆盖案例处理时间，示例 2026-10-30 14:40')
 a=p.parse_args()
 if a.trajectory is not None and a.trajectory.exists():
  p.error(f'轨迹文件已存在：{a.trajectory}')
 config=load_config(a.config); llm=config['llm']
 configure_mock_latency(config['mock'])
 path=Path(config['tracing']['directory'])/(str(uuid.uuid4())+'.jsonl')
 client=MockClient() if llm['backend']=='mock' else APIClient(llm['base_url'],llm['timeout_seconds'])
 destination = a.trajectory if a.trajectory is not None else default_path(path)
 try:
  print(run(client,path,llm['model'],config['agent']['max_turns'],llm['temperature'],llm['max_tokens'],user_message=a.question,processing_time=a.processing_time))
 except ValueError as exc:
  p.error(str(exc))
 finally:
  if path.exists():
   write_trajectory(path, destination)
   print('Session trajectory:', destination)
if __name__=='__main__': main()
