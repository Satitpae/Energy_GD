"""Frozen Windows GUI and hidden worker entry point for TOU Sender."""
import argparse
import contextlib
import io
import json
import os
import queue
from pathlib import Path
import subprocess
import sys
import threading
import time
import webbrowser
from desktop_core import acquire_lock,command_for,default_data_dir,ensure_config,is_running,save_config

VERSION='1.2.0'
def engine():
    import send
    args=sys.argv[1:];args.remove('--engine');report=None
    if '--report' in args:
        at=args.index('--report');report=Path(args[at+1]);del args[at:at+2]
    sys.argv=[sys.argv[0]]+args
    if report:
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream):code=send.main()
        report.write_text(json.dumps({'exit_code':code,'output':stream.getvalue()},ensure_ascii=False),encoding='utf-8')
        return code
    return send.main()

def main():
    if '--engine' in sys.argv:return engine()
    parser=argparse.ArgumentParser();parser.add_argument('--data-dir',type=Path);parser.add_argument('--version',action='store_true');parser.add_argument('--shutdown',action='store_true');parser.add_argument('--export-startup-task',type=Path)
    args=parser.parse_args()
    if args.export_startup_task:
        from startup_task import export_task
        user=os.environ.get('USERDOMAIN','')+'\\'+os.environ.get('USERNAME','')
        export_task(sys.executable,(args.data_dir or default_data_dir())/'config.json',user,args.export_startup_task)
        return 0
    if args.version:
        if sys.stdout:print(VERSION)
        return 0
    if args.shutdown:
        data_dir=(args.data_dir or default_data_dir()).resolve()
        if not data_dir.exists():return 0
        (data_dir/'sender.stop').touch();(data_dir/'ui-close.marker').touch()
        for _ in range(40):
            if not is_running(data_dir) and not is_running(data_dir,'ui.lock'):return 0
            time.sleep(1)
        return 1
    import tkinter as tk
    from tkinter import ttk,filedialog,messagebox
    data_dir=(args.data_dir or default_data_dir()).resolve()
    resource=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
    root=tk.Tk();root.title('GRAND DIGITAL · TOU Sender');root.geometry('780x640');root.minsize(700,480);root.configure(bg='#ffffff')
    try:
        seed=json.loads((resource/'sender-seed.json').read_text(encoding='utf-8'))
        config_path=ensure_config(data_dir,seed)
        config=json.loads(config_path.read_text(encoding='utf-8-sig'))
    except (OSError,ValueError):
        messagebox.showerror('เปิดโปรแกรมไม่ได้','อ่านการตั้งค่าไม่สำเร็จ กรุณาติดตั้งโปรแกรมใหม่ หรือแจ้งผู้ดูแลระบบ');root.destroy();return 1
    ui_lock=acquire_lock(data_dir,'ui.lock')
    if ui_lock is None:root.destroy();return 0
    (data_dir/'ui-close.marker').unlink(missing_ok=True)
    style=ttk.Style(root);style.theme_use('clam')
    style.configure('TFrame',background='white');style.configure('TLabel',background='white',foreground='#17324d',font=('Leelawadee UI',11));style.configure('TButton',font=('Leelawadee UI',10),padding=(12,9))
    style.configure('Blue.TButton',background='#2463a6',foreground='white');style.map('Blue.TButton',background=[('active','#1d528b')])
    style.configure('Orange.TButton',background='#ed7b20',foreground='white')
    style.configure('TEntry',padding=8)
    canvas=tk.Canvas(root,bg='white',highlightthickness=0)
    scrollbar=ttk.Scrollbar(root,orient='vertical',command=canvas.yview);scrollbar.pack(side='right',fill='y')
    canvas.configure(yscrollcommand=scrollbar.set);canvas.pack(side='left',fill='both',expand=True)
    frame=ttk.Frame(canvas,padding=28);window=canvas.create_window((0,0),window=frame,anchor='nw')
    frame.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
    root.bind_all('<MouseWheel>',lambda e:canvas.yview_scroll(-int(e.delta/120),'units'))
    ttk.Label(frame,text='GRAND DIGITAL',foreground='#2463a6',font=('Leelawadee UI',18,'bold')).pack(anchor='w')
    ttk.Label(frame,text='TOU Sender · โปรแกรมส่งข้อมูลพลังงาน',font=('Leelawadee UI',13)).pack(anchor='w',pady=(3,20))
    folder=tk.StringVar(value=config['folder']);status=tk.StringVar(value='กำลังตรวจสถานะ…');summary=tk.StringVar(value='ยังไม่มีประวัติส่งจากโปรแกรมนี้');rejected=tk.StringVar(value='');note=tk.StringVar(value='' if config.get('upload_token') else 'ครั้งแรก: กดตั้งค่าการเชื่อมต่อ แล้วเลือกไฟล์ config.local.json ที่ผู้ดูแลเตรียมไว้')
    ttk.Label(frame,text='โฟลเดอร์ไฟล์ TOU').pack(anchor='w')
    source=ttk.Frame(frame);source.pack(fill='x',pady=(7,14))
    entry=ttk.Entry(source,textvariable=folder);entry.pack(side='left',fill='x',expand=True)
    def browse():
        chosen=filedialog.askdirectory(initialdir=folder.get() if Path(folder.get()).is_dir() else None)
        if chosen:folder.set(chosen)
    browse_button=ttk.Button(source,text='เลือกโฟลเดอร์',command=browse);browse_button.pack(side='left',padx=(8,0))
    ttk.Label(frame,text='ปลายทาง: energy.granddigital.co.th',foreground='#64778a').pack(anchor='w')
    ttk.Separator(frame).pack(fill='x',pady=18)
    status_label=ttk.Label(frame,textvariable=status,font=('Leelawadee UI',16,'bold'),foreground='#2463a6');status_label.pack(anchor='w')
    ttk.Label(frame,textvariable=summary,wraplength=710).pack(anchor='w',pady=(9,5))
    ttk.Label(frame,textvariable=rejected,foreground='#ac5a19',wraplength=710).pack(anchor='w')
    actions=ttk.Frame(frame);actions.pack(fill='x',pady=(20,12));testing=False;starting=False;started_at=0;messages=queue.Queue()
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    def persist():
        path=Path(folder.get().strip())
        if not path.is_dir():messagebox.showerror('ไม่พบโฟลเดอร์','กรุณาเลือกโฟลเดอร์ที่มีไฟล์ TOU');return False
        config['folder']=str(path.resolve())
        try:save_config(config_path,config)
        except ValueError as e:messagebox.showerror('ยังไม่ได้ตั้งค่าการเชื่อมต่อ',str(e));return False
        return True
    def start():
        nonlocal starting,started_at
        if is_running(data_dir) or testing or starting:return
        if not persist():return
        starting=True;started_at=time.monotonic()
        try:subprocess.Popen(command_for('start',config_path),creationflags=flags,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except OSError:starting=False;note.set('เปิดตัวส่งไม่ได้ กรุณาติดตั้งโปรแกรมใหม่');return
        note.set('กำลังเริ่มตัวส่งเบื้องหลัง…');poll()
    def stop():
        if is_running(data_dir):(data_dir/'sender.stop').touch();note.set('กำลังรอให้รอบปัจจุบันจบ แล้วหยุดส่ง')
    def once():
        nonlocal testing
        if testing or starting or is_running(data_dir) or not persist():return
        testing=True;note.set('กำลังทดสอบส่งหนึ่งรอบ…');report=data_dir/'test-result.json'
        def work():
            try:
                result=subprocess.run(command_for('once',config_path)+['--report',str(report)],creationflags=flags,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                message='ทดสอบจบแล้ว ดูผลการส่งด้านบน' if result.returncode==0 else 'ทดสอบจบแล้ว มีบางรายการส่งไม่สำเร็จ ดูบันทึกผลการส่ง'
            except OSError:message='เปิดตัวส่งไม่ได้ กรุณาติดตั้งโปรแกรมใหม่'
            messages.put(message)
        threading.Thread(target=work,daemon=True).start();poll()
    def finish_test(message):
        nonlocal testing
        testing=False;note.set(message);poll()
    start_button=ttk.Button(actions,text='เริ่มส่งข้อมูล',style='Blue.TButton',command=start);start_button.pack(side='left')
    stop_button=ttk.Button(actions,text='หยุดส่ง',style='Orange.TButton',command=stop);stop_button.pack(side='left',padx=8)
    test_button=ttk.Button(actions,text='ทดสอบหนึ่งรอบ',command=once);test_button.pack(side='left')
    tools=ttk.Frame(frame);tools.pack(fill='x',pady=(0,12))
    def import_connection():
        if is_running(data_dir) or testing or starting:return
        chosen=filedialog.askopenfilename(title='เลือกไฟล์ตั้งค่าการเชื่อมต่อ',filetypes=[('ไฟล์ตั้งค่า JSON','*.json')])
        if not chosen:return
        try:
            imported=json.loads(Path(chosen).read_text(encoding='utf-8-sig'))
            if imported.get('base_url','').rstrip('/')!='https://energy.granddigital.co.th' or imported.get('site','main')!='main':raise ValueError('ไฟล์ตั้งค่าไม่ใช่หน้างานนี้')
            candidate={**config,'upload_token':imported.get('upload_token','')}
            if 'realtime' in imported:candidate['realtime']=imported['realtime']
            save_config(config_path,candidate);config.update(candidate)
            note.set('ตั้งค่าการเชื่อมต่อแล้ว กดเริ่มส่งข้อมูลได้เลย')
        except (OSError,ValueError):messagebox.showerror('อ่านไฟล์ตั้งค่าไม่ได้','กรุณาเลือกไฟล์ config.local.json ของชุด TOU Sender ที่ผู้ดูแลเตรียมไว้')
    connection_button=ttk.Button(tools,text='ตั้งค่าการเชื่อมต่อ',command=import_connection);connection_button.pack(side='left',padx=(0,8))
    def setup_startup():
        if not getattr(sys,'frozen',False):
            messagebox.showinfo('เริ่มอัตโนมัติ','ใช้ตัวติดตั้ง Windows รุ่นนี้บนเครื่องหน้างานก่อนตั้งงานอัตโนมัติ');return
        from startup_task import export_task
        user=os.environ.get('USERDOMAIN','')+'\\'+os.environ.get('USERNAME','')
        output=export_task(sys.executable,config_path,user,data_dir/'TOU-Sender-Autostart.xml')
        os.startfile(str(data_dir))
        subprocess.Popen(['mmc.exe','taskschd.msc'])
        messagebox.showinfo('ตั้งเริ่มอัตโนมัติ','ใน Task Scheduler เลือก Import Task แล้วเลือกไฟล์ TOU-Sender-Autostart.xml ที่เปิดไว้\nตรวจบัญชีผู้ใช้ เลือก Run whether user is logged on or not แล้วกด OK\nWindows จะขอรหัสผ่าน Windows (ไม่ใช่ PIN)\nงานจะเริ่มส่งเบื้องหลังหลังเปิดเครื่อง 1 นาที ไม่ต้องกดเริ่มส่ง')
    ttk.Button(tools,text='ตั้งเริ่มอัตโนมัติ',command=setup_startup).pack(side='left',padx=(0,8))
    ttk.Button(tools,text='เปิด Dashboard',command=lambda:webbrowser.open('https://energy.granddigital.co.th/dashboard/')).pack(side='left')
    def open_logs():
        path=data_dir/'logs';path.mkdir(exist_ok=True)
        os.startfile(str(path))
    ttk.Button(tools,text='บันทึกผลการส่ง',command=open_logs).pack(side='left',padx=8)
    ttk.Label(frame,textvariable=note,foreground='#64778a',wraplength=710).pack(anchor='w',pady=4)
    ttk.Separator(frame).pack(fill='x',pady=12)
    ttk.Label(frame,text='ทุก 60 วินาที: ตรวจเดือนล่าสุดของ MEA และ Solar Cell\nเดือนเก่า: ส่งซ้ำวันละครั้งในรอบแรกที่โปรแกรมทำงานวันนั้น',foreground='#64778a',wraplength=710).pack(anchor='w')
    ttk.Label(frame,text='ปิดหน้าต่างนี้ได้ ตัวส่งยังทำงานเบื้องหลัง · ใช้ปุ่มหยุดเมื่อต้องการหยุดส่ง',foreground='#64778a',font=('Leelawadee UI',9),wraplength=710).pack(anchor='w',pady=(12,0))
    ttk.Label(frame,text='Windows 10/11 · 64-bit · รุ่น '+VERSION,foreground='#8a99a8',font=('Leelawadee UI',9)).pack(anchor='w',pady=8)
    def poll():
        nonlocal starting
        running=is_running(data_dir)
        if starting and (running or time.monotonic()-started_at>5):
            starting=False
            if not running:note.set('เปิดตัวส่งไม่สำเร็จ กรุณาตรวจบันทึกผลการส่ง')
        status.set('กำลังเริ่มส่งข้อมูล…' if starting else 'กำลังทดสอบส่งข้อมูล' if testing else 'กำลังทำงานเบื้องหลัง' if running else 'หยุดส่งข้อมูล')
        for widget in [entry,browse_button,start_button,test_button,connection_button]:widget.configure(state='disabled' if running or testing or starting else 'normal')
        stop_button.configure(state='normal' if running and not testing else 'disabled')
        log=data_dir/'logs/tou-sender.log'
        if log.exists():
            with log.open('rb') as f:f.seek(max(0,log.stat().st_size-12000));lines=f.read().decode('utf-8',errors='replace').splitlines()
            for line in reversed(lines):
                if '{' not in line:continue
                try:
                    result=json.loads(line[line.index('{'):]);summary.set('ล่าสุด '+line[:19]+'\nส่งสำเร็จ '+str(result['sent'])+' · ไม่เปลี่ยน '+str(result['unchanged'])+' · รอรายวัน '+str(result.get('history_wait',0))+' · ไม่สำเร็จ '+str(result['failed']));break
                except (ValueError,KeyError):continue
        state=data_dir/'state.json'
        if state.exists():
            try:
                count=len(json.loads(state.read_text(encoding='utf-8')).get('rejected',{}));rejected.set('มี '+str(count)+' ไฟล์ที่รูปแบบไม่ผ่าน — ดูรายละเอียดในบันทึกผลการส่ง' if count else '')
            except (OSError,ValueError):pass
    def tick():
        if (data_dir/'ui-close.marker').exists():root.destroy();return
        while not messages.empty():finish_test(messages.get_nowait())
        try:poll()
        finally:root.after(2000,tick)
    try:tick();root.mainloop()
    finally:ui_lock.close()
    return 0

if __name__=='__main__':raise SystemExit(main())
