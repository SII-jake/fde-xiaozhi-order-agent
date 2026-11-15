import json, os, urllib.request
from .trajectory import estimate_usage
from .tools import ORDERS
from .mock_latency import simulate_latency
# 应用在证据齐备（含物流复查）后追加到消息列表末尾的答复要求。
# 定义在 client.py 是为了避免 app/client 循环导入：app 用它构造追加的
# 用户消息，Mock 用它识别最终答复请求。
REPLY_REQUIREMENTS = (
    '证据和物流复查结果已齐备，请现在给出最终答复，要求如下：\n'
    '1. 按「结论与证据、预计时间、下一步、政策依据」四项输出。\n'
    '2. 每项最多一句。\n'
    '3. 同一条事实或规则只写一次。\n'
    '4. 预计日期须注明不能保证；依据不足时写「待确认」。\n'
    '5. 延误超过三天才进入补偿资格审核。\n'
    '6. 证据冲突时须升级人工。'
)
FINAL_ANSWERS = {
 'delayed':
  '结论与证据：订单 A1024 承诺 10 月 28 日送达，仓库记录显示 10 月 27 日已交接承运商，物流轨迹显示 10 月 28 日在中转站发生延误，包裹仍在运输途中。\n'
  '预计时间：最新轨迹预计 10 月 30 日送达，该日期不能保证。\n'
  '下一步：建议联系承运商跟进中转站滞留。\n'
  '政策依据：依据《订单延误处理指引》（P-DELAY），超过承诺送达日期三天才进入补偿资格审核，本次延误一天尚不满足。',
 'warehouse':
  '结论与证据：订单 A1025 承诺 10 月 28 日送达，仓库记录显示 10 月 27 日已打包但尚未交接承运商，订单状态为待出库。\n'
  '预计时间：待确认。\n'
  '下一步：建议联系仓库调查延误原因。\n'
  '政策依据：依据《订单延误处理指引》（P-DELAY），晚于承诺日期的订单应按证据联系仓库或承运商。',
 'conflicting':
  '结论与证据：订单 A1026 的仓库交接记录与物流轨迹存在冲突，延误原因无法确认。\n'
  '预计时间：待确认。\n'
  '下一步：暂不向客户给出结论，转人工跟进。\n'
  '政策依据：依据《订单延误处理指引》（P-DELAY），证据冲突或无法确认延误原因时须升级人工调查。',
}
class MockClient:
 """Scripted fixture, NOT an LLM. Usage is estimated for classroom replay."""
 def __init__(self):
  self.order_id = None
  self.step = 0
 def complete(self,request):
  simulate_latency('model')
  if self.order_id is None:
   question=next((m.get('content','') for m in request['messages'] if m.get('role')=='user'),'')
   # The mock uses fixture IDs from the message to simulate the model's choice.
   words=''.join(c if c.isascii() and c.isalnum() else ' ' for c in question.upper()).split()
   orders=[order_id for order_id in ORDERS if order_id in words]
   if len(orders)!=1:
    message={'role':'assistant','content':'请在问题中写明一笔有效订单的订单号，例如 A1024。'}
    return {'id':'mock-clarification','model':request['model'],'choices':[{'message':message,'finish_reason':'stop'}],
            'usage':estimate_usage(request,message,None),'teaching_mock':True,'usage_source':'mock_estimate'}
   self.order_id=orders[0]
  o=ORDERS[self.order_id]
  # 调查阶段照常取证。答复要求由应用在证据与物流复查返回后追加到
  # 消息列表末尾；Mock 仅在该条用户消息出现在末尾时才给出最终答复。
  last=request['messages'][-1] if request['messages'] else {}
  if last.get('role')=='user' and last.get('content')==REPLY_REQUIREMENTS:
   # 末次请求（只剩撰写最终答复）不提供任何工具；若仍携带工具，
   # 说明应用的按阶段工具逻辑有问题，宁可报错也不静默放行。
   if request.get('tools'):
    raise RuntimeError('最终答复请求仍携带工具定义：请检查应用的按阶段工具逻辑。')
   answer=FINAL_ANSWERS[o['kind']]
   message={'role':'assistant','content':answer}; reason='stop'
  else:
   # 订单已由应用预取并随用户消息注入，运单号已知：首次响应同时发出
   # 查仓库和首次查物流两条工具调用；两项结果都返回后再继续调查；
   # 答复前复查物流。
   steps=[
    [('get_warehouse_events',{'order_id':self.order_id}),('get_tracking',{'tracking_number':o['tracking_number']})],
    [('search_policy',{'query':'订单延误'})],
    [('get_policy_document',{'policy_id':'P-DELAY'})],
    [('get_tracking',{'tracking_number':o['tracking_number']})],
   ]
   if self.step>=len(steps):
    raise RuntimeError('Mock 已完成取证步骤，但答复要求消息尚未追加：请检查应用的注入逻辑。')
   batch=steps[self.step]
   message={'role':'assistant','content':None,'tool_calls':[{'id':'tool-'+str(self.step)+'-'+str(index),'type':'function','function':{'name':name,'arguments':json.dumps(arguments,ensure_ascii=False)}} for index,(name,arguments) in enumerate(batch)]}; reason='tool_calls'
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
