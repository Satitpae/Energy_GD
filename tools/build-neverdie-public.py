"""Public main-site read-only patch. No credentials in archive."""
from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[1]
public='domains/energy.granddigital.co.th/public_html/'
files={
 'api/index.php':(root/'neverdie/index.php').read_bytes(),
 'api/public-policy.php':(root/'neverdie/public-policy.php').read_bytes(),
 'dashboard/app.js':(root/'dashboard/app.js').read_bytes(),
 'dashboard/mode.js':b'window.EMS_ONLINE=true;window.EMS_API_PHP=true;window.EMS_PUBLIC_READ=true;\n',
 'dashboard/index.html':(root/'dashboard/index.html').read_text(encoding='utf-8').replace('app.js?v=3','app.js?v=4').replace('src="mode.js"','src="mode.js?v=4"').encode()
}
with zipfile.ZipFile(root/'.local/neverdie-public.zip','w') as z:
 for name,data in files.items():
  info=zipfile.ZipInfo(public+name);info.create_system=3;info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
print('Public read-only update prepared: 5 files; no secrets.')
