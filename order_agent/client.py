import json, os, urllib.request
from .tools import ORDERS
from .mock_latency import simulate_latency
class MockClient:
 """Scripted fixture, NOT an LLM. Usage is intentionally unavailable."""
 def __init__(self, order_id, *, optimized=False):
  self.order_id = order_id
  self.step = 0
  self.optimized = optimized
 def complete(self,request):
  simulate_latency('model')
  o=ORDERS[self.order_id]
  steps=[('get_order',{'order_id':self.order_id}),('get_warehouse_events',{'order_id':self.order_id}),('get_tracking',{'tracking_number':o['tracking_number']}),('search_policy',{'query':'订单延误'}),('get_policy_document',{'policy_id':'P-DELAY'}),('get_tracking',{'tracking_number':o['tracking_number']})]
  last = request.get('messages', [{}])[-1].get('content') or ''
  optimized = self.optimized
  if optimized:
   if last.startswith('先在同一次响应'):
    selected = [steps[1], steps[3]]
   elif last.startswith('读取检索到的政策正文'):
    selected = [steps[4]] + ([steps[5]] if o['status']=='in_transit' else [])
   else:
    selected = []
  else:
   selected = steps[self.step:self.step+1]
  if selected:
   calls = [
    {'id':f'tool-{self.step}-{index}' if optimized else f'tool-{self.step}',
     'type':'function','function':{'name':name,'arguments':json.dumps(arguments,ensure_ascii=False)}}
    for index,(name,arguments) in enumerate(selected)
   ]
   message={'role':'assistant','content':None,'tool_calls':calls}; reason='tool_calls'
  else:
   answer={'delayed':'运输中转延误；仓库已交接。联系承运商跟进，预计10月30日送达但不保证；尚未达到补偿审核门槛。依据：仓库记录、物流轨迹、P-DELAY。','warehouse':'订单尚未交接承运商，应联系仓库调查，不应承诺物流送达时间。依据：订单和仓库记录。','conflicting':'现有证据存在冲突，无法可靠判断原因，应升级人工调查。依据：订单冲突标记和物流记录。'}[o['kind']]
   if optimized:
    answer = {
     'delayed':'结论：中转站延误。预计时间：10月30日，非保证。建议：联系承运商，暂不承诺补偿。政策依据：《订单延误处理指引》。',
     'warehouse':'结论：尚未出库。预计时间：待确认。建议：联系仓库。政策依据：《订单延误处理指引》。',
     'conflicting':'结论：仓库与物流证据冲突。预计时间：待确认。建议：升级人工。政策依据：《订单延误处理指引》。',
    }[o['kind']]
   message={'role':'assistant','content':answer}; reason='stop'
  self.step+=1
  return {'id':'mock-'+str(self.step),'model':request['model'],'choices':[{'message':message,'finish_reason':reason}], 'usage':None, 'teaching_mock':True}
class APIClient:
 def __init__(self,base_url,timeout_seconds=120):
  self.url=base_url.rstrip('/')+'/chat/completions'; self.timeout_seconds=timeout_seconds
 def complete(self,request):
  headers={'Content-Type':'application/json'}
  if os.getenv('LLM_API_KEY'): headers['Authorization']='Bearer '+os.environ['LLM_API_KEY']
  req=urllib.request.Request(self.url,data=json.dumps(request).encode(),headers=headers)
  with urllib.request.urlopen(req,timeout=self.timeout_seconds) as response: return json.load(response)
