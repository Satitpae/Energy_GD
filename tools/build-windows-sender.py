"""Build a credential-free x64 application and NSIS installer."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PRIVATE=ROOT/'.local'
APP=PRIVATE/'windows-build/TOUSender'
RELEASE=ROOT/'releases/TOU-Sender-1.2.0'
RELEASE.mkdir(parents=True,exist_ok=True)
seed=PRIVATE/'sender-seed.json'
seed.write_text(json.dumps({'base_url':'https://energy.granddigital.co.th','site':'main','folder':'C:/HView/System'}),encoding='utf-8')
assert set(json.loads(seed.read_text()))=={'base_url','site','folder'}
build_python=ROOT/'.cache/sender-build/Scripts/python.exe'
command=[str(build_python),'-m','PyInstaller','--noconfirm','--onedir','--windowed','--name','TOUSender','--paths',str(ROOT/'uploader'),'--paths',str(ROOT/'.cache/mysql-client'),'--hidden-import','startup_task','--hidden-import','realtime_sync','--hidden-import','realtime_source','--collect-all','pymysql','--add-data',str(seed)+';.','--distpath',str(PRIVATE/'windows-build'),'--workpath',str(ROOT/'.cache/sender-pyinstaller'),'--specpath',str(ROOT/'.cache'),str(ROOT/'uploader/desktop_app.py')]
subprocess.run(command,cwd=ROOT,check=True)
guide='''# TOU Sender 1.2.0 สำหรับ Windows 10/11 แบบ 64-bit

ไม่ต้องติดตั้ง Python และไม่ต้องใช้สิทธิ์ผู้ดูแลระบบ

1. เปิด TOU-Sender-Setup-1.2.0-x64.exe แล้วทำตามขั้นตอนติดตั้ง
2. เปิด TOU Sender จาก Desktop หรือ Start Menu
3. ครั้งแรกกด “ตั้งค่าการเชื่อมต่อ” เลือกไฟล์ config.local.json ที่ผู้ดูแลเตรียมให้แยกต่างหาก
4. ตรวจโฟลเดอร์ C:\\HView\\System แล้วกด “เริ่มส่งข้อมูล”

ทุก60วินาทีตรวจเดือนล่าสุดของ D01=MEA และ D02=Solar ส่งเมื่อเนื้อหาเปลี่ยนเท่านั้น เดือนเก่าส่งซ้ำวันละครั้งในรอบแรกที่โปรแกรมทำงานวันนั้น เน็ตขัดข้องลองใหม่รอบถัดไป เมื่อเปิดใช้ Realtime ในไฟล์ตั้งค่า จะอ่าน MySQL แบบอ่านอย่างเดียวและส่งทุก60วินาที พร้อมทยอยส่งวันย้อนหลังตั้งแต่ history_start ไม่แก้ไฟล์ TOU หรือข้อมูล MySQL ต้นฉบับ

ปิดหน้าต่างได้ ตัวส่งยังทำงานเบื้องหลัง เปิดโปรแกรมอีกครั้งเพื่อตรวจสถานะหรือกดหยุด หากต้องการทดสอบหนึ่งรอบให้หยุดตัวส่งก่อน

ค่าตั้ง ประวัติ และ log อยู่ที่ %LOCALAPPDATA%\\GrandDigital\\TOUSender อัปเดต/ถอนการติดตั้งจะเก็บส่วนนี้ไว้ ตั้งเริ่มอัตโนมัติได้ผ่านปุ่ม ตั้งเริ่มอัตโนมัติ แล้วนำเข้า Task Scheduler ตามคู่มือ

ก่อนย้ายไปเครื่องจริง ให้หยุดตัวส่งบนเครื่องทดสอบก่อน เพื่อไม่ให้ส่งไฟล์ชื่อเดียวกันทับกัน

ตั้งค่า realtime.enabled, realtime.mysql และ realtime.history_start ในไฟล์ config.local.json แล้วนำเข้าผ่านปุ่มตั้งค่าการเชื่อมต่อ รหัส MySQL เก็บเฉพาะเครื่องหน้างาน ห้ามเผยแพร่ไฟล์ตั้งค่า

ตัวติดตั้งไม่มี Token หรือรหัส MySQL ฝังอยู่ ไฟล์ config.local.json มีสิทธิ์ส่งข้อมูลและควรเก็บภายในบริษัท โปรแกรมรุ่นนี้ยังไม่มีลายเซ็นดิจิทัล การทดสอบทำบน Windows11 x64; ยังไม่ได้ทดสอบบนเครื่องหน้างานจริง

14ไฟล์เดิมที่ header/ข้อมูลไม่ผ่าน API ยังไม่ถือว่าส่งสำเร็จ ดูรายชื่อในบันทึกผลการส่ง
'''
(APP/'README-TH.md').write_text(guide,encoding='utf-8')
third='TOU Sender uses Python (PSF license), Tcl/Tk (BSD-style), PyInstaller (GPL with bootloader distribution exception), and NSIS (zlib/libpng and component licenses).\n\n'
license_path=Path(sys.base_prefix)/'LICENSE.txt'
if license_path.exists():third+=license_path.read_text(encoding='utf-8',errors='replace')
(APP/'THIRD-PARTY.txt').write_text(third,encoding='utf-8')
manifest=PRIVATE/'sender-uninstall-files.nsh'
lines=['!macro RemoveInstalledFiles']
for p in APP.rglob('*'):
 if p.is_file():lines.append('  Delete "$INSTDIR\\'+str(p.relative_to(APP)).replace('$','$$')+'"')
for p in sorted((p for p in APP.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):lines.append('  RMDir "$INSTDIR\\'+str(p.relative_to(APP)).replace('$','$$')+'"')
lines.append('!macroend');manifest.write_text('\n'.join(lines),encoding='utf-8-sig')
output=RELEASE/'TOU-Sender-Setup-1.2.0-x64.exe'
compiler=ROOT/'.cache/nsis-download/nsis-3.11/makensis.exe'
subprocess.run([str(compiler),'/INPUTCHARSET','UTF8','/DAPPDIR='+str(APP),'/DOUTFILE='+str(output),'/DUNINSTALL_MANIFEST='+str(manifest),str(ROOT/'tools/tou-sender-installer.nsi')],cwd=ROOT,check=True)
shutil.copy2(APP/'README-TH.md',RELEASE/'คู่มือติดตั้ง-TOU-Sender.md')
(RELEASE/'SHA256SUMS.txt').write_text(hashlib.sha256(output.read_bytes()).hexdigest()+'  '+output.name+'\n',encoding='ascii')
print('Installer ready:',output,'bytes:',output.stat().st_size)
