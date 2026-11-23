import json, os, socket, sys, threading, unittest, urllib.error, urllib.request
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.coach import CoachError, catalog, validate_input, candidates, output_schema, provider_call, recommend, validate_output
from api import recommend as endpoint
from scripts.serve import LocalHandler

def user(**kw):return {'question':'멜메탈 덱을 추천해 주세요.','ownedCards':'멜탄, 멜메탈 ex','style':'defensive','type':'전체','consent':True,**kw}
def answer(decks=None):return {'summary':'검증용 응답입니다.','recommendations':[{'deckId':(decks or catalog()['decks'])[0]['id'],'reason':'등록된 자료를 바탕으로 한 제안입니다.','playSteps':['진화 준비를 확인하세요.'],'cautions':['최신 성능은 미확인입니다.']}],'unknowns':['현재 티어는 미확인입니다.']}
class Reply:
 def __init__(self,p):self.body=json.dumps(p).encode()
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self,n):return self.body[:n]
class CoachTests(unittest.TestCase):
 def test_new_recipes_match_public_evidence_and_keep_ratings_separate(self):
  evidence=json.loads((ROOT/'docs/new-recipe-evidence.json').read_text(encoding='utf-8'))['selected']
  new=[d for d in catalog()['decks'] if d['id'].startswith('verified-')]
  self.assertEqual(len(new),3)
  for d,e in zip(new,evidence):
   expected={('PROMO-A' if c['set']=='P-A' else c['set'])+'-'+c['number']:c['count'] for kind in ('pokemon','trainer') for c in e['decklist'][kind]}
   self.assertEqual({c['id']:c['quantity'] for c in d['cards']},expected)
   self.assertIsNone(d['tier']);self.assertIsNone(d['selfRating'])
   self.assertEqual(d['checkedAt'],'2026-11-18')
   self.assertIn(d['guideRating']['tier'],(1,2))
   self.assertEqual(d['guideRating']['sourceName'],'GameWith')
   self.assertIn('미확인',d['format'])
  ids={d['id'] for d in candidates(validate_input(user(question='메가나무킹 ex 덱 운영을 알려줘.')))}
  self.assertIn('verified-sceptile-greninja',ids)
 def test_required_consent_and_length(self):
  for p,code in [(user(question=' '),'empty_question'),(user(consent=False),'consent_required'),(user(question='a'*801),'invalid_input'),(user(type='bad'),'invalid_type')]:
   with self.subTest(code=code),self.assertRaises(CoachError) as cm:validate_input(p)
   self.assertEqual(cm.exception.code,code)
 def test_real_recipes_and_public_copy(self):
  self.assertEqual(catalog(),json.loads((ROOT/'public/data/catalog.json').read_text(encoding='utf-8-sig')));self.assertEqual(len(catalog()['decks']),10)
  for d in catalog()['decks']:
   self.assertIsNone(d['tier']);self.assertEqual(sum(c['quantity'] for c in d['cards']),20);self.assertTrue(all(c['quantity'] in (1,2) for c in d['cards']))
 def test_schema_only_allows_filtered_server_ids(self):
  ds=candidates(validate_input(user(type='강철')));self.assertTrue(all(d['type']=='강철' for d in ds));self.assertLessEqual(len(ds),4)
  self.assertEqual(output_schema([d['id'] for d in ds])['properties']['recommendations']['items']['properties']['deckId']['enum'],[d['id'] for d in ds])
 def test_unknown_duplicates_and_invented_recipe_rejected(self):
  for mode in ('unknown','duplicate','recipe'):
   a=answer()
   if mode=='unknown':a['recommendations'][0]['deckId']='invented'
   elif mode=='duplicate':a['recommendations']*=2
   else:a['recommendations'][0]['cards']=[{'id':'fake','quantity':99}]
   with self.assertRaises(CoachError):validate_output(a,catalog()['decks'])
 def test_valid_reply_has_original_twenty_cards_and_sources(self):
  r=recommend(user(),caller=lambda u,ds:(answer(ds),'test-model'));d=r['recommendations'][0]['deck'];self.assertEqual(sum(c['quantity'] for c in d['cards']),20);self.assertTrue(d['sourceUrl'].startswith('https://'));self.assertIsNone(d['tier'])
 def test_missing_key_and_disabled_never_contact_provider(self):
  for env,code in [({'GEMINI_API_KEY':'','AI_ENABLED':'true'},'not_configured'),({'GEMINI_API_KEY':'test','AI_ENABLED':'false'},'disabled')]:
   with patch.dict(os.environ,env),patch('urllib.request.urlopen') as call,self.assertRaises(CoachError) as cm:provider_call(validate_input(user()),catalog()['decks'])
   self.assertEqual(cm.exception.code,code);call.assert_not_called()
 def test_rest_contract(self):
  ds=candidates(validate_input(user()));p={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(answer(ds))}]}}]}
  with patch.dict(os.environ,{'GEMINI_API_KEY':'test-not-a-real-key','AI_ENABLED':'true'}),patch('urllib.request.urlopen',return_value=Reply(p)) as call:a,model=provider_call(validate_input(user()),ds)
  req=call.call_args.args[0];body=json.loads(req.data);self.assertTrue(req.full_url.startswith('https://generativelanguage.googleapis.com/v1beta/models/'));self.assertEqual(body['generationConfig']['responseMimeType'],'application/json');self.assertNotIn('test-not-a-real-key',req.full_url);self.assertEqual(req.get_header('X-goog-api-key'),'test-not-a-real-key');self.assertEqual(call.call_args.kwargs['timeout'],25);self.assertEqual(a,answer(ds))
 def test_upstream_errors_are_sanitized(self):
  for err,code,status in [(urllib.error.HTTPError('url',401,'secret-details',{},None),'provider_auth',503),(urllib.error.HTTPError('url',429,'quota',{},None),'provider_busy',503),(socket.timeout(),'timeout',504)]:
   with patch.dict(os.environ,{'GEMINI_API_KEY':'private-test-key','AI_ENABLED':'true'}),patch('urllib.request.urlopen',side_effect=err),self.assertRaises(CoachError) as cm:provider_call(validate_input(user()),catalog()['decks'])
   self.assertEqual((cm.exception.code,cm.exception.status),(code,status));self.assertNotIn('private-test-key',str(cm.exception));self.assertNotIn('secret-details',str(cm.exception))
 def test_non_object_provider_envelope_is_rejected(self):
  with patch.dict(os.environ,{'GEMINI_API_KEY':'test','AI_ENABLED':'true'}),patch('urllib.request.urlopen',return_value=Reply([])),self.assertRaises(CoachError) as cm:provider_call(validate_input(user()),catalog()['decks'])
  self.assertEqual(cm.exception.code,'invalid_response')
 def test_refusal_and_incomplete(self):
  for p,code in [({'candidates':[{'finishReason':'MAX_TOKENS'}]},'incomplete'),({'promptFeedback':{'blockReason':'SAFETY'}},'refused')]:
   with patch.dict(os.environ,{'GEMINI_API_KEY':'test','AI_ENABLED':'true'}),patch('urllib.request.urlopen',return_value=Reply(p)),self.assertRaises(CoachError) as cm:provider_call(validate_input(user()),catalog()['decks'])
   self.assertEqual(cm.exception.code,code)
class HTTPTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),partial(LocalHandler,directory=str(ROOT/'public')));cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.base='http://127.0.0.1:'+str(cls.server.server_port)
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
 def setUp(self):endpoint._hits.clear()
 def post(self,body,headers=None):
  req=urllib.request.Request(self.base+'/api/recommend',data=body,headers=headers or {'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(req) as r:return r.status,json.load(r)
  except urllib.error.HTTPError as r:return r.code,json.load(r)
 def test_json_and_content_type_errors(self):
  status,body=self.post(b'{}');self.assertEqual(status,400);self.assertEqual(body['error']['code'],'empty_question');self.assertEqual(self.post(b'{bad')[0],400);self.assertEqual(self.post(b'{}',{'Content-Type':'text/plain'})[0],415)
 def test_success_over_http_uses_original_recipe(self):
  result=recommend(user(),caller=lambda u,ds:(answer(ds),'mock-model'))
  with patch.object(endpoint,'recommend',return_value=result):status,body=self.post(json.dumps(user()).encode())
  self.assertEqual(status,200);self.assertEqual(sum(c['quantity'] for c in body['recommendations'][0]['deck']['cards']),20)
 def test_health_never_exposes_key(self):
  with patch.dict(os.environ,{'GEMINI_API_KEY':'secret-local-test','AI_ENABLED':'true'}):
   with urllib.request.urlopen(self.base+'/api/recommend') as r:body=json.load(r)
  self.assertEqual(body,{'ready':True,'mode':'live'})
 def test_missing_key_is_503(self):
  with patch.dict(os.environ,{'GEMINI_API_KEY':'','AI_ENABLED':'true'}):status,body=self.post(json.dumps(user()).encode())
  self.assertEqual(status,503);self.assertEqual(body['error']['code'],'not_configured')
 def test_cross_origin_and_large_request(self):
  self.assertEqual(self.post(b'{}',{'Content-Type':'application/json','Origin':'https://other.example'})[0],403);self.assertEqual(self.post(b' '*8193)[0],413)
 def test_rate_limit(self):
  with patch.dict(os.environ,{'GEMINI_API_KEY':'','AI_ENABLED':'true'}):
   for _ in range(5):self.post(json.dumps(user()).encode())
   status,_=self.post(json.dumps(user()).encode())
  self.assertEqual(status,429)
 def test_static_root_does_not_expose_private_files(self):
  for path in ('/.env.local','/backend/coach.py','/scripts/serve.py','/docs/SERVICE_PLAN.md'):
   with self.subTest(path=path),self.assertRaises(urllib.error.HTTPError) as cm:urllib.request.urlopen(self.base+path)
   self.assertEqual(cm.exception.code,404)
  with urllib.request.urlopen(self.base+'/') as r:self.assertIn('포켓 덱 코치',r.read().decode('utf-8-sig'))
if __name__=='__main__':unittest.main()

