import base64
import hashlib
import json
import secrets
import zipfile
from pathlib import Path

root=Path(__file__).resolve().parents[1]
private=root/'.local'
keypath=private/'neverdie-setup-key.txt'
key=keypath.read_text() if keypath.exists() else secrets.token_urlsafe(32)
keypath.write_text(key)
library=base64.b64encode((root/'neverdie/api-lib.php').read_bytes()).decode()
script='''<?php
ini_set('display_errors','0');
header('Cache-Control: no-store');header('Content-Type: application/json');
if($_SERVER['REQUEST_METHOD']!=='POST'){http_response_code(404);echo '{}';exit;}
$data=json_decode(file_get_contents('php://input'),true);
if(!is_array($data)||!isset($data['setup_key'])||!is_string($data['setup_key'])||!hash_equals('SETUP_HASH',hash('sha256',$data['setup_key']))){http_response_code(403);echo '{}';exit;}
foreach(['view_token','upload_token'] as $k)if(!isset($data[$k])||!is_string($data[$k])||!preg_match('/^[A-Za-z0-9_-]{32,100}$/D',$data[$k])){http_response_code(400);echo '{}';exit;}
if($data['view_token']===$data['upload_token']){http_response_code(400);echo '{}';exit;}
$dir=dirname(__DIR__,4).'/.php/granddigital-ems-tou-private';
if(file_exists($dir)){http_response_code(409);echo '{"error":"Already provisioned"}';exit;}
if(!is_writable(dirname($dir))||!mkdir($dir,0700)){http_response_code(503);echo '{"error":"Private area unavailable"}';exit;}
$config=['view_token'=>$data['view_token'],'upload_token'=>$data['upload_token'],'data_dir'=>$dir.'/data','max_file_bytes'=>131072,'max_storage_bytes'=>104857600,'max_month_bytes'=>419430400,'max_day_requests'=>1000];
$library=base64_decode('LIBRARY');
if(file_put_contents($dir.'/api-lib.php',$library)!==strlen($library)||file_put_contents($dir.'/config.php',"<?php\\nreturn ".var_export($config,true).";\\n")===false){http_response_code(503);echo '{"error":"Provision failed"}';exit;}
chmod($dir.'/api-lib.php',0600);chmod($dir.'/config.php',0600);
echo json_encode(['ok'=>true,'php_version'=>PHP_VERSION]);
'''.replace('SETUP_HASH',hashlib.sha256(key.encode()).hexdigest()).replace('LIBRARY',library)
(private/'neverdie-setup.php').write_text(script,encoding='utf-8')
with zipfile.ZipFile(private/'neverdie-api-fix.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for name,data in [('index.php',(root/'neverdie/index.php').read_text()),('setup.php',script)]:
        info=zipfile.ZipInfo('domains/energy.granddigital.co.th/public_html/api/'+name)
        info.create_system=3;info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED
        archive.writestr(info,data)
print('Private provisioning package prepared; no tokens printed.')
