import json, os, urllib.request
from .trajectory import estimate_usage
from .tools import ORDERS
from .mock_latency import simulate_latency
class MockClient:
 """Scripted fixture, NOT an LLM. Usage is estimated for classroom replay."""
 def __init__(self, order_id, *, optimized=False):
  self.order_id = order_id
  self.step = 0
  self.optimized = optimized
 def complete(self,request):
  simulate_latency('model')
  o=ORDERS[self.order_id]
  steps=[('get_order',{'order_id':self.order_id}),('get_warehouse_events',{'order_id':self.order_id}),('get_tracking',{'tracking_number':o['tracking_number']}),('search_policy',{'query':'订单延误'}),('get_policy_document',{'policy_id':'P-DELAY'}),('get_tracking',{'tracking_number':o['tracking_number']})]
  last = (request.get('messages') or [{}])[-1].get('content') or ''
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
   answer={'delayed':'我先查了订单 A1024，确认承诺送达日期为 10 月 28 日，关联运单是 TA1024。接着核查仓库记录，看到仓库已于 10 月 27 日交接给承运商。第一次查物流时，轨迹显示包裹在中转站发生延误，预计 10 月 30 日送达。随后我检索并阅读《订单延误处理指引》，确认延误超过三天才进入补偿资格审核。最后我复查了同一个运单，最新节点和预计日期没有变化。综合以上记录，运输中转延误是当前原因。建议联系承运商跟进，10 月 30 日是预计日期，不能保证，暂不承诺补偿。','warehouse':'订单尚未交接承运商，应联系仓库调查，不应承诺物流送达时间。依据：订单和仓库记录。','conflicting':'现有证据存在冲突，无法可靠判断原因，应升级人工调查。依据：订单冲突标记和物流记录。'}[o['kind']]
   if optimized:
    answer = {
     'delayed':'结论与证据：物流显示包裹在中转站延误。\n预计时间：10 月 30 日送达，不能保证。\n下一步：联系承运商跟进。\n政策依据：《订单延误处理指引》规定延误超过三天才进入补偿审核。',
     'warehouse':'结论：尚未出库。预计时间：待确认。建议：联系仓库。政策依据：《订单延误处理指引》。',
     'conflicting':'结论：仓库与物流证据冲突。预计时间：待确认。建议：升级人工。政策依据：《订单延误处理指引》。',
    }[o['kind']]
   if o['kind']=='delayed' and request['messages'][-1].get('content') == '按结论与证据、预计时间、下一步、政策依据答复，每项最多一句。':
    answer='结论与证据：物流显示包裹在中转站延误。\n预计时间：10 月 30 日送达，不能保证。\n下一步：联系承运商跟进。\n政策依据：《订单延误处理指引》规定延误超过三天才进入补偿审核。'
   message={'role':'assistant','content':answer}; reason='stop'
  usage = estimate_usage(request, message, getattr(self, 'previous_request', None))
  self.previous_request = request
  self.step+=1
  return {'id':'mock-'+str(self.step),'model':request['model'],'choices':[{'message':message,'finish_reason':reason}], 'usage':usage, 'teaching_mock':True, 'usage_source':'mock_estimate'}
class APIClient:
 def __init__(self,base_url,timeout_seconds=120):
  self.url=base_url.rstrip('/')+'/chat/completions'; self.timeout_seconds=timeout_seconds
 def complete(self,request):
  headers={'Content-Type':'application/json'}
  if os.getenv('LLM_API_KEY'): headers['Authorization']='Bearer '+os.environ['LLM_API_KEY']
  req=urllib.request.Request(self.url,data=json.dumps(request).encode(),headers=headers)
  with urllib.request.urlopen(req,timeout=self.timeout_seconds) as response: return json.load(response)
