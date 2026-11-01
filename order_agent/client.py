import json, os, urllib.request
from .tools import ORDERS
class MockClient:
 """Scripted fixture, NOT an LLM. Usage is intentionally unavailable."""
 def __init__(self,order_id): self.order_id=order_id; self.step=0
 def complete(self,request):
  o=ORDERS[self.order_id]
  steps=[('get_order',{'order_id':self.order_id}),('get_warehouse_events',{'order_id':self.order_id}),('get_tracking',{'tracking_number':o['tracking_number']}),('search_policy',{'query':'订单延误'}),('get_policy_document',{'policy_id':'P-DELAY'}),('get_tracking',{'tracking_number':o['tracking_number']})]
  if self.step<len(steps):
   n,a=steps[self.step]; message={'role':'assistant','content':None,'tool_calls':[{'id':'tool-'+str(self.step),'type':'function','function':{'name':n,'arguments':json.dumps(a,ensure_ascii=False)}}]}; reason='tool_calls'
  else:
   answer={'delayed':'运输中转延误；仓库已交接。联系承运商跟进，预计10月30日送达但不保证；尚未达到补偿审核门槛。依据：仓库记录、物流轨迹、P-DELAY。','warehouse':'订单尚未交接承运商，应联系仓库调查，不应承诺物流送达时间。依据：订单和仓库记录。','conflicting':'现有证据存在冲突，无法可靠判断原因，应升级人工调查。依据：订单冲突标记和物流记录。'}[o['kind']]
   message={'role':'assistant','content':answer}; reason='stop'
  self.step+=1
  return {'id':'mock-'+str(self.step),'model':request['model'],'choices':[{'message':message,'finish_reason':reason}], 'usage':None, 'teaching_mock':True}
class APIClient:
 def __init__(self,base_url): self.url=base_url.rstrip('/')+'/chat/completions'
 def complete(self,request):
  headers={'Content-Type':'application/json'}
  if os.getenv('LLM_API_KEY'): headers['Authorization']='Bearer '+os.environ['LLM_API_KEY']
  req=urllib.request.Request(self.url,data=json.dumps(request).encode(),headers=headers)
  with urllib.request.urlopen(req,timeout=120) as response: return json.load(response)
