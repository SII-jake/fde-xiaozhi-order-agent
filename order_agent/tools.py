"""Thirteen read-only mock business tools (draft creation has no external side effects)."""
import json
from pathlib import Path
from .mock_latency import simulate_latency
ORDERS = json.loads((Path(__file__).resolve().parents[1]/"materials/orders.json").read_text())
POLICY = {"id":"P-DELAY", "text":"晚于承诺日期可跟进仓库或承运商；超过三天才进入补偿资格审核。预计送达时间不是保证。证据冲突须升级人工。"}
POLICY_DOCUMENT = Path(__file__).resolve().parents[1] / "materials/order-delay-policy.md"
POLICY_DOCUMENT_TEXT = POLICY_DOCUMENT.read_text(encoding="utf-8")

def slim_policy_document(markdown):
 """Model-facing policy excerpt: policy ID and body sections only.
 Cover page, table of contents and drafting notes are dropped; the
 适用范围/例外/补偿门槛 clauses live in the body and are kept."""
 policy_id=None; body_start=None
 lines=markdown.splitlines()
 for index,line in enumerate(lines):
  if policy_id is None and '文件编号' in line and '：' in line:
   policy_id=line.split('：',1)[1].strip()
  if line.strip()=='## 正文':
   body_start=index+1
 if policy_id is None or body_start is None: return markdown
 body='\n'.join(lines[body_start:]).strip()
 return '文件编号：'+policy_id+'\n\n'+body


def combined_order_and_tracking(order_id):
    """Read-only composite lookup: order first, then tracking via the order's tracking number."""
    order = execute("get_order", {"order_id": order_id})
    tracking_number = order.get("tracking_number")
    tracking = (
        execute("get_tracking", {"tracking_number": tracking_number})
        if tracking_number else None
    )
    return {"order": order, "tracking": tracking}


SPECS = {
 "get_order":("查询订单详情", "order_id"),
 "get_order_and_tracking":("查订单和物流：先查订单，再用订单返回的运单号查物流，一并返回订单信息和物流记录", "order_id"),
 "get_order_items":("查询商品明细", "order_id"),
 "get_customer_profile":("查询客户资料和会员等级", "customer_id"),
 "get_customer_order_history":("查询客户历史订单", "customer_id"),
 "get_warehouse_events":("查询仓库及交接事件", "order_id"),
 "get_tracking":("查询物流轨迹", "tracking_number"),
 "get_carrier_notices":("查询区域物流公告", "region"),
 "get_support_history":("查询订单客服记录", "order_id"),
 "search_policy":("搜索政策片段", "query"),
 "get_policy_document":("读取完整政策", "policy_id"),
 "check_compensation_eligibility":("检查补偿资格", "order_id"),
 "create_escalation_draft":("创建待人工确认的工单草稿，不提交", "order_id")}
def definitions():
 return [{"type":"function","function":{"name":n,"description":d,"parameters":{"type":"object","properties":{k:{"type":"string"}},"required":[k],"additionalProperties":False}}} for n,(d,k) in SPECS.items()]
def execute(name,args):
 if name not in SPECS: raise ValueError("Unknown tool: "+name)
 key=SPECS[name][1]
 if set(args)!={key} or not isinstance(args[key],str): raise ValueError("Invalid arguments")
 simulate_latency('tool')
 value=args[key]
 if key=='order_id' and value not in ORDERS: raise ValueError('Unknown order')
 o=ORDERS.get(value)
 if name=='get_order': return {k:v for k,v in o.items() if k not in ['items','warehouse_events','tracking_events','support_history']}
 if name=='get_order_and_tracking': return combined_order_and_tracking(value)
 if name=='get_order_items': return o['items']
 if name=='get_customer_profile': return {'customer_id':value,'tier':'standard','region':'Shanghai'}
 if name=='get_customer_order_history': return [x for x in ORDERS.values() if x['customer_id']==value]
 if name=='get_warehouse_events': return o['warehouse_events']
 if name=='get_tracking':
  matches=[x for x in ORDERS.values() if x['tracking_number']==value]
  if not matches: raise ValueError('Unknown tracking number')
  return {'events':matches[0]['tracking_events'],'evidence_conflict':matches[0]['evidence_conflict']}
 if name=='get_carrier_notices': return {'region':value,'notices':['部分中转线路延误，具体订单以轨迹为准']}
 if name=='get_support_history': return o['support_history']
 if name=='search_policy': return {'matches':[POLICY]}
 if name=='get_policy_document':
  if value!=POLICY['id']: raise ValueError('Unknown policy')
  # The model receives the slim excerpt (policy ID + body); tracing
  # keeps the full Markdown via POLICY_DOCUMENT_TEXT below.
  return slim_policy_document(POLICY_DOCUMENT_TEXT)
 if name=='check_compensation_eligibility': return {'eligible':False,'reason':'案例延误一天，尚未达到超过三天的审核门槛','policy_id':POLICY['id']}
 return {'draft_id':'DRAFT-'+value,'status':'awaiting_human_confirmation','submitted':False}
