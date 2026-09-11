"""Exercise authenticated downloads through the real HTTP worker."""
import hashlib
import io
import json
import urllib.error
import urllib.request
import unittest
import zipfile
from test_connector import JOB, WorkerHTTPTests
import server


class ExportDownloadTests(unittest.TestCase):
    setUp = WorkerHTTPTests.setUp
    tearDown = WorkerHTTPTests.tearDown
    def request_bytes(self, path, token=None):
        request = urllib.request.Request('http://127.0.0.1:%d%s' % (self.http.server_port,path),
            headers={'Authorization':'Bearer '+(self.config['token'] if token is None else token)})
        try:response=urllib.request.urlopen(request,timeout=3)
        except urllib.error.HTTPError as error:response=error
        with response:return response.status, response.headers, response.read()

    def make_export(self):
        folder=server.JOBS/JOB;folder.mkdir();(folder/'textures').mkdir()
        payloads={'model.fbx':b'fixture FBX', 'model.obj':b'mtllib model.mtl\n',
                  'model.mtl':b'newmtl skin\nmap_Kd textures/skin.png\n',
                  'textures/skin.png':b'fixture PNG'}
        records={}
        for name,data in payloads.items():
            (folder/name).write_bytes(data)
            records[name]={'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
        report={'fbx':{'status':'ready','files':[records['model.fbx']]},
                'obj':{'status':'ready','files':[records['model.obj'],records['model.mtl']]},
                'textures':[records['textures/skin.png']]}
        (folder/'result.json').write_text(json.dumps({'interchange_exports':report}))
        (folder/'reference-private.jpg').write_bytes(b'not an export')
        with server.database() as db:
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,0,0)',(JOB,'Fixture','succeeded','ready'))
        return folder,report,payloads

    def test_download_authentication_obj_archive_and_file_integrity(self):
        folder,_,payloads=self.make_export();base='/v1/jobs/'+JOB+'/exports'
        self.assertEqual(self.request_bytes(base+'/obj',token='invalid')[0],401)
        code,headers,body=self.request_bytes(base+'/obj')
        self.assertEqual(code,200);self.assertEqual(headers['Cache-Control'],'no-store')
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            self.assertEqual(set(archive.namelist()),{'model.obj','model.mtl','textures/skin.png'})
            self.assertEqual(archive.read('textures/skin.png'),payloads['textures/skin.png'])
        self.assertEqual(self.request_bytes(base+'/fbx')[2],payloads['model.fbx'])
        self.assertEqual(self.request_bytes(base+'/../../config.json')[0],404)
        (folder/'model.fbx').write_bytes(b'changed after export')
        self.assertEqual(self.request_bytes(base+'/fbx')[0],409)
        formats=json.loads(self.request_bytes(base)[2])['formats']
        self.assertEqual([x['format'] for x in formats],['obj'])

    def test_provider_pbr_archive_is_complete_private_and_hash_checked(self):
        folder, report, _ = self.make_export()
        (folder / 'provider-textures').mkdir()
        data = b'offline normal map transport fixture'
        name = 'provider-textures/00-normal.png'
        (folder / name).write_bytes(data)
        report['pbr'] = {'status':'ready','files':[{'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}]}
        (folder / 'result.json').write_text(json.dumps({'interchange_exports':report}))
        url = '/v1/jobs/' + JOB + '/exports/pbr'
        self.assertEqual(self.request_bytes(url,token='invalid')[0],401)
        code, headers, body = self.request_bytes(url)
        self.assertEqual(code,200)
        self.assertEqual(headers['Content-Type'],'application/zip')
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            self.assertEqual(archive.namelist(),[name])
            self.assertEqual(archive.read(name),data)
        (folder / name).write_bytes(b'changed')
        self.assertEqual(self.request_bytes(url)[0],409)

    def test_failed_jobs_missing_textures_and_symlinks_are_not_downloadable(self):
        folder,report,_=self.make_export();base='/v1/jobs/'+JOB+'/exports/'
        (folder/'textures/skin.png').unlink()
        self.assertEqual(self.request_bytes(base+'obj')[0],409)
        (folder/'textures/skin.png').symlink_to(folder/'reference-private.jpg')
        self.assertEqual(self.request_bytes(base+'obj')[0],409)
        report['fbx']['status']='failed'
        (folder/'result.json').write_text(json.dumps({'interchange_exports':report}))
        self.assertEqual(self.request_bytes(base+'fbx')[0],409)
        with server.database() as db:db.execute("UPDATE jobs SET state='failed' WHERE id=?",(JOB,))
        self.assertEqual(self.request_bytes(base.rstrip('/'))[0],409)
