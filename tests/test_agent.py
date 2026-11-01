import json,tempfile,unittest
from pathlib import Path
from order_agent.app import run
from order_agent.client import MockClient
from order_agent.tools import definitions,execute,SPECS
from order_agent.analyze import summarize
class AgentTests(unittest.TestCase):
 def test_trace_reconstructs_business_flow(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'trace.jsonl';answer=run(MockClient('A1024'),'A1024',p)
   events=[json.loads(x) for x in p.read_text().splitlines()]
   self.assertIn('运输',answer)
   requests=[e for e in events if e['event']=='llm_request']
   self.assertEqual(len(requests),7)
   self.assertEqual(sum(e['event']=='tool_execution' for e in events),6)
   self.assertTrue(any(m['role']=='tool' for m in requests[-1]['request']['messages']))
   self.assertEqual(len(summarize(p)['calls']),7)
   self.assertIsNone(summarize(p)['calls'][0]['usage'])
 def test_tools(self):
  self.assertEqual(len(definitions()),12)
  for name,(_,key) in SPECS.items():
   value={'order_id':'A1024','customer_id':'C001','tracking_number':'TA1024','region':'Shanghai','query':'delay','policy_id':'P-DELAY'}[key]
   self.assertIsNotNone(execute(name,{key:value}))
  self.assertFalse(execute('create_escalation_draft',{'order_id':'A1024'})['submitted'])
 def test_limit_is_recorded(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'trace.jsonl'
   with self.assertRaises(RuntimeError):run(MockClient('A1024'),'A1024',p,max_turns=1)
   self.assertEqual(json.loads(p.read_text().splitlines()[-1])['status'],'turn_limit')
 def test_unknown_order(self):
  with self.assertRaises(ValueError):execute('get_order',{'order_id':'missing'})
if __name__=='__main__':unittest.main()
