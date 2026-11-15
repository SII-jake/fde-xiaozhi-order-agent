import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from order_agent.mock_latency import simulate_latency, validate_settings
from order_agent.app import resolve_order_id, run
from order_agent import app
from order_agent.client import MockClient
from order_agent.tools import definitions,execute,SPECS,POLICY_DOCUMENT_TEXT,slim_policy_document
from order_agent.analyze import summarize
QUESTION = '订单 A1024 应该昨天到货，现在还没收到。请调查并建议下一步。'

class AgentTests(unittest.TestCase):
 def setUp(self):
  sleeper=patch('order_agent.mock_latency.time.sleep')
  self.sleep=sleeper.start(); self.addCleanup(sleeper.stop)
 def test_model_and_tool_simulate_waiting(self):
  with patch('order_agent.mock_latency.random.uniform', return_value=0.123) as uniform:
   MockClient().complete({'model':'mock-latency-test','messages':[{'role':'user','content':QUESTION}]})
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
   p=Path(d)/'trace.jsonl';answer=run(MockClient(),p,user_message=QUESTION)
   events=[json.loads(x) for x in p.read_text().splitlines()]
   self.assertIn('运输',answer)
   prefetch=[e for e in events if e['event']=='application_prefetch']
   requests=[e for e in events if e['event']=='llm_request']
   self.assertEqual(len(prefetch),1)
   self.assertEqual(prefetch[0]['name'],'get_order')
   self.assertEqual(prefetch[0]['result']['order_id'],'A1024')
   self.assertEqual(prefetch[0]['result']['tracking_number'],'TA1024')
   self.assertEqual(len(requests),5)
   self.assertEqual(sum(e['event']=='tool_execution' for e in events),5)
   self.assertIn('应用预取',requests[0]['request']['messages'][1]['content'])
   self.assertIn('TA1024',requests[0]['request']['messages'][1]['content'])
   self.assertIn(QUESTION,requests[0]['request']['messages'][1]['content'])
   self.assertTrue(any(m['role']=='tool' for m in requests[-1]['request']['messages']))
   self.assertEqual(len(summarize(p)['calls']),5)
   self.assertGreater(summarize(p)['calls'][0]['usage']['prompt_tokens'], 0)
 def test_prefetched_order_is_reused_without_tool_call(self):
  with tempfile.TemporaryDirectory() as d:
   evidence=[]
   run(MockClient(),Path(d)/'trace.jsonl',user_message=QUESTION,on_tool=evidence.append)
   self.assertEqual([e['name'] for e in evidence],['get_warehouse_events','get_tracking','search_policy','get_policy_document','get_tracking'])
   self.assertFalse(any(e['name']=='get_order' for e in evidence))
 def test_first_response_calls_warehouse_and_tracking_in_parallel(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'trace.jsonl';evidence=[]
   answer=run(MockClient(),p,user_message=QUESTION,on_tool=evidence.append)
   events=[json.loads(x) for x in p.read_text().splitlines()]
   responses=[e for e in events if e['event']=='llm_response']
   first_calls=responses[0]['response']['choices'][0]['message']['tool_calls']
   self.assertEqual([c['function']['name'] for c in first_calls],['get_warehouse_events','get_tracking'])
   self.assertNotEqual(first_calls[0]['id'],first_calls[1]['id'])
   tracking=[e for e in evidence if e['name']=='get_tracking']
   self.assertEqual(len(tracking),2)
   self.assertIn('TA1024',evidence[1]['arguments'])
   self.assertIn('运输',answer)
 def test_business_answer_and_browser_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   evidence=[]
   answer=run(MockClient(),Path(d)/'trace.jsonl',user_message=QUESTION,on_tool=evidence.append)
   self.assertIn('运输',answer)
   self.assertEqual(len(evidence),5)
   self.assertEqual(evidence[0]['name'],'get_warehouse_events')
   self.assertEqual(evidence[1]['result']['events'][0]['event'],'中转站延误')
 def test_slim_policy_document_keeps_id_and_body(self):
  slim=execute('get_policy_document',{'policy_id':'P-DELAY'})
  self.assertIn('文件编号：P-DELAY',slim)
  self.assertIn('适用范围与证据核对',slim)
  self.assertIn('补偿审核和人工升级',slim)
  self.assertIn('超过承诺送达日期三天',slim)
  for excluded in ('## 目录','编制说明','分发范围','生效日期'):
   self.assertNotIn(excluded,slim)
  self.assertLess(len(slim),len(POLICY_DOCUMENT_TEXT))
 def test_policy_document_trace_keeps_markdown_original(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'trace.jsonl';evidence=[]
   run(MockClient(),p,user_message=QUESTION,on_tool=evidence.append)
   events=[json.loads(x) for x in p.read_text().splitlines()]
   tool_events=[e for e in events if e['event']=='tool_execution' and e['name']=='get_policy_document']
   self.assertEqual(len(tool_events),1)
   self.assertEqual(tool_events[0]['result'],POLICY_DOCUMENT_TEXT)
   policy_tool=[e for e in evidence if e['name']=='get_policy_document']
   self.assertEqual(policy_tool[0]['result'],POLICY_DOCUMENT_TEXT)
   requests=[e for e in events if e['event']=='llm_request']
   policy_messages=[m for m in requests[-1]['request']['messages'] if m.get('role')=='tool']
   policy_content=[m['content'] for m in policy_messages if '文件编号：P-DELAY' in m['content']]
   self.assertTrue(policy_content)
   self.assertIn('适用范围与证据核对',policy_content[0])
   self.assertNotIn('编制说明',policy_content[0])
 def test_tools(self):
  self.assertEqual(len(definitions()),13)
  for name,(_,key) in SPECS.items():
   value={'order_id':'A1024','customer_id':'C001','tracking_number':'TA1024','region':'Shanghai','query':'delay','policy_id':'P-DELAY'}[key]
   self.assertIsNotNone(execute(name,{key:value}))
  self.assertFalse(execute('create_escalation_draft',{'order_id':'A1024'})['submitted'])
 def test_combined_order_and_tracking_tool(self):
  combined=execute('get_order_and_tracking',{'order_id':'A1024'})
  self.assertEqual(combined['order']['order_id'],'A1024')
  self.assertEqual(combined['order']['tracking_number'],'TA1024')
  self.assertEqual(combined['tracking']['events'][0]['event'],'中转站延误')
  combined_names={tool['function']['name'] for tool in definitions()}
  self.assertIn('get_order_and_tracking',combined_names)
  untouched=execute('get_order',{'order_id':'A1024'})
  self.assertEqual(untouched['tracking_number'],'TA1024')
 def test_combined_tool_returns_empty_tracking_before_dispatch(self):
  combined=execute('get_order_and_tracking',{'order_id':'A1025'})
  self.assertEqual(combined['order']['status'],'awaiting_dispatch')
  self.assertEqual(combined['tracking']['events'],[])
 @unittest.skipUnless(hasattr(app,'History'), 'Complete history is the lesson1-end exercise')
 def test_limit_is_recorded(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'trace.jsonl'
   with self.assertRaises(RuntimeError):run(MockClient(),p,max_turns=1,user_message=QUESTION)
   self.assertEqual(json.loads(p.read_text().splitlines()[-1])['status'],'turn_limit')
 def test_order_number_comes_from_question(self):
  self.assertEqual(resolve_order_id('订单a1025没到，请查一下 A1025。'), 'A1025')
  for question, error in (
      ('我的包裹还没到', '注明订单号'),
      ('运单 TA1024 怎么了', '注明订单号'),
      ('A1024 和 A1025 都没到', '一次只能调查一笔'),
      ('A9999 怎么还没到', '没有找到订单'),
  ):
   with self.subTest(question=question), self.assertRaisesRegex(ValueError, error):
    resolve_order_id(question)
 def test_unknown_order(self):
  with self.assertRaises(ValueError):execute('get_order',{'order_id':'missing'})
if __name__=='__main__':unittest.main()
