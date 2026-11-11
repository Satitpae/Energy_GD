"""Build a private DirectAdmin ZIP with only new project paths."""
import json
import secrets
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / '.local'
PRIVATE.mkdir(exist_ok=True)
secret_file = PRIVATE / 'neverdie-secrets.json'
if secret_file.exists():
    tokens = json.loads(secret_file.read_text(encoding='utf-8'))
else:
    tokens = {'view_token': secrets.token_urlsafe(32), 'upload_token': secrets.token_urlsafe(32)}
    secret_file.write_text(json.dumps(tokens, indent=2), encoding='utf-8')

home_private = 'granddigital-ems-tou-private'
public = 'domains/energy.granddigital.co.th/public_html'
def add_text(package, name, text):
    info = zipfile.ZipInfo(name)
    info.create_system = 3
    info.external_attr = ((0o100600 if name.startswith(home_private+'/') else 0o100644) << 16)
    info.compress_type = zipfile.ZIP_DEFLATED
    package.writestr(info, text)
names = ['index.html','style.css','app.js','combined-app.js','combined.mjs','sender-status.mjs','parser.mjs','tou.mjs','excel.mjs','view.mjs','trial.mjs','selection.mjs']
archive = PRIVATE / 'neverdie-trial.zip'
config = "<?php\nreturn [\n" + ''.join("  '" + k + "' => '" + v + "',\n" for k,v in tokens.items())
config += "  'data_dir' => __DIR__.'/data',\n  'max_file_bytes' => 131072,\n  'max_storage_bytes' => 104857600,\n  'max_month_bytes' => 419430400,\n  'max_day_requests' => 1000,\n];\n"
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as package:
    for name in names:
        text = (ROOT / 'dashboard' / name).read_text(encoding='utf-8')
        if name == 'index.html':
            text = text.replace('ยังไม่ได้เชื่อม Cloudflare', 'Hosting บริษัท').replace('อ่านทุกเดือนจากโฟลเดอร์ TOU File for test', 'ไฟล์ออนไลน์จากหน้างาน')
        add_text(package,public+'/dashboard/'+name, text)
    add_text(package,public+'/dashboard/mode.js','window.EMS_ONLINE=true; window.EMS_API_PHP=true; window.EMS_PUBLIC_READ=true;\n')
    add_text(package,public+'/index.html','<!doctype html><html lang="th"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=/dashboard/"><title>Energy Dashboard</title></head><body><a href="/dashboard/">เปิด Dashboard</a></body></html>')
    add_text(package,public+'/api/index.php',(ROOT/'neverdie'/'index.php').read_text(encoding='utf-8'))
    add_text(package,public+'/api/sender-status.php',(ROOT/'neverdie'/'sender-status.php').read_text(encoding='utf-8'))
    add_text(package,public+'/api/public-policy.php',(ROOT/'neverdie'/'public-policy.php').read_text(encoding='utf-8'))
    add_text(package,home_private+'/api-lib.php',(ROOT/'neverdie'/'api-lib.php').read_text(encoding='utf-8'))
    add_text(package,home_private+'/config.php',config)
    add_text(package,home_private+'/.htaccess','Require all denied\n')
    add_text(package,public+'/.htaccess', '''Options -Indexes
AddType application/javascript .mjs .js
DirectoryIndex index.html
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteCond %{HTTP:Authorization} ^(.+)$
RewriteRule .* - [E=HTTP_AUTHORIZATION:%1]
</IfModule>
<IfModule mod_headers.c>
Header always set X-Content-Type-Options "nosniff"
Header always set Referrer-Policy "no-referrer"
Header always set X-Frame-Options "DENY"
Header always set Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
</IfModule>
''')

(PRIVATE/'neverdie-view-token.txt').write_text('Site: main\nView token:\n'+tokens['view_token']+'\n',encoding='utf-8')
uploader = {'base_url':'https://energy.granddigital.co.th','site':'main','folder':'../TOU File for test','upload_token':tokens['upload_token'],'api_style':'php','state_file':'state-neverdie.json','interval_seconds':60}
(ROOT/'uploader'/'config.neverdie.local.json').write_text(json.dumps(uploader,indent=2),encoding='utf-8')
manifest_path = PRIVATE/'neverdie-install-manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {'created_subdomain':False}
manifest.update({'public_dir':public,'private_dir':home_private,'archive':archive.name,'hostname':'energy.granddigital.co.th'})
manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Prepared private Neverdie archive; token values not printed.')
print('Public destination: '+public)
print('Private destination outside web root: '+home_private)
