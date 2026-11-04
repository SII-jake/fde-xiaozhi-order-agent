import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from order_agent.mock_latency import simulate_latency, validate_settings
from order_agent.app import run
from order_agent import app
from order_agent.client import MockClient
from order_agent.tools import definitions,execute,SPECS
from order_agent.analyze import summarize
class AgentTests(unittest.TestCase):
 def setUp(self):
  sleeper=patch('order_agent.mock_latency.time.sleep')
  self.sleep=sleeper.start(); self.addCleanup(sleeper.stop)
 def test_model_and_tool_simulate_waiting(self):
  with patch('order_agent.mock_latency.random.uniform', return_value=0.123) as uniform:
   MockClient('A1024').complete({'model':'teaching-mock'})
   execute('get_order', {'order_id':'A1024'})
  self.assertEqual(uniform.call_args_list[0].args, (0.3, 0.9))
  self.assertEqual(uniform.call_args_list[1].args, (0.05, 0.2))
  self.assertEqual(self.sleep.call_count, 2)
  self.sleep.assert_called_with(0.123)
 def test_invalid_mock_delay_is_rejected(self):
  for bounds in ([-1, 1], [2, 1], [0, float('nan')], [0, float('inf')]):
   with self.assertRaises(ValueError):validate_settings({'model_delay_seconds':bounds})
 @unittest.skipUnless(hasattr(app,'History'), 'Complete history is the lesson1-end exercise')
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
 def test_business_answer_and_browser_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   evidence=[]
   answer=run(MockClient('A1024'),'A1024',Path(d)/'trace.jsonl',on_tool=evidence.append)
   self.assertIn('运输',answer)
   self.assertEqual(len(evidence),6)
   self.assertEqual(evidence[0]['result']['tracking_number'],'TA1024')
 def test_tools(self):
  self.assertEqual(len(definitions()),12)
  for name,(_,key) in SPECS.items():
   value={'order_id':'A1024','customer_id':'C001','tracking_number':'TA1024','region':'Shanghai','query':'delay','policy_id':'P-DELAY'}[key]
   self.assertIsNotNone(execute(name,{key:value}))
  self.assertFalse(execute('create_escalation_draft',{'order_id':'A1024'})['submitted'])
 @unittest.skipUnless(hasattr(app,'History'), 'Complete history is the lesson1-end exercise')
 def test_limit_is_recorded(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'trace.jsonl'
   with self.assertRaises(RuntimeError):run(MockClient('A1024'),'A1024',p,max_turns=1)
   self.assertEqual(json.loads(p.read_text().splitlines()[-1])['status'],'turn_limit')
 def test_unknown_order(self):
  with self.assertRaises(ValueError):execute('get_order',{'order_id':'missing'})
if __name__=='__main__':unittest.main()
