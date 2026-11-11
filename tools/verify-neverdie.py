"""Verify only the isolated Neverdie TOU deployment; never print tokens."""
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE='https://energy.granddigital.co.th'
tokens=json.loads((ROOT/'.local/neverdie-secrets.json').read_text(encoding='utf-8'))

def request(path,token=None,body=None):
    headers={'Authorization':'Bearer '+token} if token else {}
    if body is not None:headers['Content-Type']='application/octet-stream'
    req=urllib.request.Request(BASE+path,headers=headers,data=body)
    try:
        response=urllib.request.urlopen(req,timeout=30)
    except urllib.error.HTTPError as error:
        response=error
    with response:
        return response.code,response.headers,response.read()

def api(action,name=None,token=None,body=None,site='main'):
    params={'action':action,'site':site}
    if name:params['name']=name
    return request('/api/index.php?'+urllib.parse.urlencode(params),token,body)

if __name__=='__main__':
    for path in ['/dashboard/','/dashboard/parser.mjs','/dashboard/tou.mjs']:
        status,headers,body=request(path)
        print(path,status,headers.get('Content-Type'),len(body))
        assert status==200
        if path.endswith('.mjs'):assert 'javascript' in headers.get('Content-Type','')
    assert api('tou-files')[0]==200,'Main site read must be public'
    assert api('tou-files',site='other')[0]==401,'Other sites must not be public'
    assert api('upload','D01Oct26.tou',body=b'no')[0]==401,'Anonymous upload must be denied'
    print('Main site public read enabled; other sites and uploads protected.')
    for name in ['D01Sep26.tou','D02Sep26.tou','D01Oct26.tou','D02Oct26.tou']:
        data=(ROOT/'TOU File for test'/name).read_bytes()
        status,_,ack=api('upload',name,tokens['upload_token'],data)
        print('Upload',name,status)
        assert status==200,'Upload failed: HTTP '+str(status)
        assert json.loads(ack)['ok'] is True
        status,_,stored=api('tou-file',name)
        assert status==200 and stored==data,'Original bytes must round trip'
    assert api('tou-files',token=tokens['upload_token'])[0]==200
    assert api('upload','D01Oct26.tou',tokens['view_token'],b'no')[0]==401
    assert api('upload','D01Oct26.tou',tokens['upload_token'],b'no')[0]==400
    assert api('upload','D01Oct26.tou',tokens['upload_token'],b'x'*131073)[0]==413
    assert api('tou-file','D01Oct26.tou',tokens['view_token'],site='other')[0]==404
    status,_,listed=api('tou-files',token=tokens['view_token'])
    assert status==200 and len(json.loads(listed)['files'])==4
    for path in ['/granddigital-ems-tou-private/config.php','/data/main/D01Oct26.tou','/neverdie-trial.zip']:
        assert request(path)[0] in (403,404),'Private file publicly accessible: '+path
    print('Live checks passed: 4 files publicly readable byte-for-byte, upload token required, site isolation, invalid/oversize rejection, private config not public.')
