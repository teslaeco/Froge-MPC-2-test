import importlib.util,json,tempfile,unittest,threading,urllib.request,urllib.error,time
from pathlib import Path
from http.server import ThreadingHTTPServer
spec=importlib.util.spec_from_file_location('bridge',Path(__file__).with_name('server.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ID='24b50b39-c029-44b3-90ae-5bc3f998f39f'
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.b=m.Bridge(self.root,'https://teslaeco.github.io',self.root/'bridge-state');self.b.upstream=lambda path,data=None:{'ready':True,'connectorVersion':33,'state':'succeeded'}
 def tearDown(self):self.tmp.cleanup()
 def test_prompt_limit(self):
  with self.assertRaises(ValueError):m.validate_job({'id':ID,'prompt':'x','agentInstructions':'x'*10000})
 def test_idempotent_queue(self):
  req={'id':ID,'prompt':'cube','agentInstructions':'make cube'};self.b.enqueue(req);self.b.enqueue(req)
  with self.b.db() as db:self.assertEqual(db.execute('select count(*) from jobs').fetchone()[0],1)
  with self.assertRaises(ValueError):self.b.enqueue(dict(req,prompt='house'))
 def test_archive_keeps_source_and_hash(self):
  self.b.enqueue({'id':ID,'prompt':'cube','agentInstructions':'make cube'});folder=self.root/'state/jobs'/ID;folder.mkdir(parents=True);(folder/'model.glb').write_bytes(b'glTF'+b'0000'*20);(folder/'secret-key.txt').write_text('not copied')
  path=self.b.archive(ID);self.assertEqual(path.read_bytes(),(folder/'model.glb').read_bytes());self.assertFalse((path.parent/'secret-key.txt').exists());self.assertEqual(self.b.archive(ID),path)
 def test_symlink_rejected(self):
  target=self.root/'outside';target.write_text('data');link=self.root/'link';link.symlink_to(target)
  with self.assertRaises(ValueError):m.plain(link,self.root)
 def test_auth_and_origin(self):
  server=ThreadingHTTPServer(('127.0.0.1',0),m.handler(self.b));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_address[1])+'/api/health'
  try:
   with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(url)
   self.assertEqual(e.exception.code,401)
   req=urllib.request.Request(url,headers={'Authorization':'Bearer '+self.b.token,'Origin':self.b.origin})
   with urllib.request.urlopen(req) as r:self.assertTrue(json.load(r)['ready']);self.assertEqual(r.headers['Access-Control-Allow-Origin'],self.b.origin)
   req=urllib.request.Request(url,headers={'Authorization':'Bearer '+self.b.token,'Origin':'https://other.example'})
   with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(req)
   self.assertEqual(e.exception.code,403)
  finally:server.shutdown();server.server_close()
if __name__=='__main__':unittest.main()
