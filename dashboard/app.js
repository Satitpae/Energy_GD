import {parseTou} from './parser.mjs';
import {dashboardView} from './view.mjs';
import {rawExcel} from './excel.mjs';
import {periodsForMeter,datasetForSelection,energyComparison} from './selection.mjs';
const $=id=>document.getElementById(id),datasets=new Map();
const online=window.EMS_ONLINE===true;
const publicRead=online&&window.EMS_PUBLIC_READ===true;
let viewToken=online?sessionStorage.getItem('ems-view-token')??'':'',site=online?sessionStorage.getItem('ems-site')??'main':'main';
if(publicRead){viewToken='';site='main';sessionStorage.removeItem('ems-view-token');sessionStorage.removeItem('ems-site');}
function apiUrl(path,scope){const url=new URL(path,location.origin);if(online)url.searchParams.set('site',scope.site);if(window.EMS_API_PHP===true&&url.pathname.startsWith('/api/')){const action=url.pathname.slice(5);url.pathname='/api/index.php';url.searchParams.set('action',action);}return url.pathname+url.search;}
function apiFetch(path,scope){return fetch(apiUrl(path,scope),{cache:'no-store',headers:online&&!publicRead?{Authorization:'Bearer '+scope.token}:{}});}
const fmt=x=>x===null||x===undefined?'—':x.toLocaleString('en-US',{maximumFractionDigits:3});
const dateLabel=date=>new Date(date+'T00:00:00Z').toLocaleDateString('th-TH',{day:'numeric',month:'short',year:'numeric',calendar:'gregory',timeZone:'UTC'});
const node=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
let current=null,selectedMeter='D01',folderFiles=new Set(),loadingFiles=false;
function options(){
 const entries=[...datasets.values()],old=$('period').value;
 if(!periodsForMeter(entries,selectedMeter).length)selectedMeter=entries[0]?.period.device.toUpperCase()??'D01';
 $('period').replaceChildren();for(const p of periodsForMeter(entries,selectedMeter))$('period').add(new Option(p.label??p.key,p.key));
 if([...$('period').options].some(o=>o.value===old))$('period').value=old;
 for(const [id,meter]of [['meterMEA','D01'],['meterSolar','D02']]){const b=$(id),active=selectedMeter===meter;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));b.disabled=!periodsForMeter(entries,meter).length;}
 render();
}
function importFile(buffer,name){const data=parseTou(buffer,name);if(!['D01','D02'].includes(data.period.device.toUpperCase()))throw Error('รองรับมิเตอร์ D01 (MEA) และ D02 (Solar Cell) เท่านั้น');for(const [key,d]of datasets)if(d.period.device.toUpperCase()===data.period.device.toUpperCase()&&d.period.key===data.period.key)datasets.delete(key);datasets.set(name,data);}
async function loadSamples(){
 if(online&&!publicRead&&!viewToken){$('message').textContent='กรอกโทเคนดูข้อมูลเพื่อเปิด Dashboard';return;}
 if(loadingFiles)return;loadingFiles=true;const scope={site,token:viewToken};for(const id of ['loadSamples','refreshFiles'])$(id).disabled=true;if(online)for(const e of $('accessForm').elements)e.disabled=true;
 try{
  const response=await apiFetch('/api/tou-files',scope);if(!response.ok)throw Error(online?(response.status===401?'โทเคนดูข้อมูลไม่ถูกต้อง':'ยังอ่านข้อมูลออนไลน์ไม่ได้ กรุณาลองใหม่'):'อ่านรายการไฟล์ไม่ได้ กรุณาเปิดผ่าน start-dashboard.cmd รุ่นล่าสุด');
  const {files}=await response.json(),errors=[];
  for(const name of folderFiles)datasets.delete(name);folderFiles=new Set();
  for(const {name}of files){try{const r=await apiFetch(online?'/api/tou-file?name='+encodeURIComponent(name):'/TOU%20File%20for%20test/'+encodeURIComponent(name),scope);if(!r.ok)throw Error(`HTTP ${r.status}`);importFile(await r.arrayBuffer(),name);folderFiles.add(name);}catch(e){errors.push(`${name}: ${e.message}`);}}
  options();
  if(!datasets.size){current=null;$('periodText').textContent='ยังไม่มีไฟล์ข้อมูล';for(const id of ['energy','peak','latestTime','latestDate','energyHint','peakAt','coverage'])$(id).textContent='—';for(const id of ['demandChart','energyChart','pieChart','pieLegend','dailyTable','dailyTotal','rawTable','rawDay','auditSummary'])$(id).replaceChildren();$('export').disabled=true;$('dailyExport').disabled=true;}
  $('message').textContent=errors.length?'โหลดไฟล์บางรายการไม่ได้\n'+errors.join('\n'):!datasets.size?'ไม่พบไฟล์ TOU ในโฟลเดอร์ กรุณาเพิ่มไฟล์หรือเลือกไฟล์ด้านล่าง':'';
  $('fileCount').textContent=`${files.length} ไฟล์${online?'ออนไลน์':'ในโฟลเดอร์'}`;
 }catch(error){$('message').textContent=error.message;}
 finally{loadingFiles=false;for(const id of ['loadSamples','refreshFiles'])$(id).disabled=false;if(online)for(const e of $('accessForm').elements)e.disabled=false;}
}
function render(){const data=datasetForSelection(datasets.values(),selectedMeter,$('period').value);if(!data)return;$('message').textContent='';current=dashboardView(data,data.period.start,data.period.end);const v=current;
 $('periodText').textContent=`${v.meter} · ${data.period.label}`;
 $('energy').textContent=fmt(v.total.energy[3]);$('energyHint').textContent=data.period.label;
 $('peak').textContent=fmt(v.peak?.demand);$('peakAt').textContent=v.peak?`${dateLabel(v.peak.date)} · เวลา ${v.peak.time} น.`:'ไม่มีข้อมูลในช่วงที่เลือก';
 $('latestTime').textContent=v.audit.lastReading?.slice(11)??'—';$('latestDate').textContent=v.audit.lastReading?dateLabel(v.audit.lastReading.slice(0,10)):'ยังไม่มีข้อมูล';
 const noData=v.days.filter(d=>d.status==='ไม่มีข้อมูล').length;
 $('coverage').textContent=`ข้อมูลในไฟล์ถึง ${v.audit.lastReading?dateLabel(v.audit.lastReading.slice(0,10))+' เวลา '+v.audit.lastReading.slice(11)+' น.':'—'} · พบช่องข้อมูลศูนย์บางช่วง${noData?' · '+noData+' วันในช่วงที่เลือกยังไม่มีข้อมูล':''} — ดูรายละเอียดใน “ตรวจสอบข้อมูล”`;
 $('chartMeter').textContent=v.meter;renderCharts(v);renderDaily(v);renderComparison(data.period);
 const old=$('rawDay').value;$('rawDay').replaceChildren();for(const d of v.days)$('rawDay').add(new Option(dateLabel(d.date),d.date));if(v.days.some(d=>d.date===old))$('rawDay').value=old;renderRaw();
 const a=v.audit;$('auditSummary').replaceChildren(...[
  `ไฟล์ ${a.name} · ${fmt(a.bytes)} ไบต์ · ${fmt(a.totalRows)} แถว`,
  `ข้อมูลจริง ${a.firstReading} ถึง ${a.lastReading} · แถวในเดือน ${fmt(a.monthRows)} · แถวนอกเดือน ${a.outsideMonth}`,
  `ศูนย์ทั้งคู่ภายในช่วงข้อมูล ${a.internalZeroRows} แถว · Energy ศูนย์แต่มี Demand ${a.energyZeroWithDemand} แถว · ศูนย์ท้ายไฟล์ ${a.trailingZeroRows} แถว`,
  `เลขสะสมที่ไม่ใช่ศูนย์ลดลง ${a.nonzeroRegisterDecreases.length} ครั้ง · ค่าติดลบ ${a.negativeReadings} แถว`,
  'ช่องศูนย์อาจเป็นข้อมูลขาดหรือค่าศูนย์จริง ไม่เติมค่าทดแทนอัตโนมัติ ข้อมูลล่าสุดเป็นเวลาจากไฟล์ ไม่ใช่สถานะการเชื่อมต่อมิเตอร์'
 ].map(t=>node('p',t)));
 $('export').disabled=!v.rows.length;$('dailyExport').disabled=!v.days.length;
}
function renderDaily(v){$('dailyTable').replaceChildren();for(const d of v.days){const tr=node('tr');if(d.status!=='ครบขอบเวลา')tr.className='partial';else if(d.holiday)tr.className='holiday';for(const t of [dateLabel(d.date),...d.energy.map(fmt),...d.demand.map(fmt),d.status])tr.append(node('td',t));$('dailyTable').append(tr);}const tr=node('tr');for(const t of ['รวม',...v.total.energy.map(fmt),...v.total.demand.map(fmt),'รวมเฉพาะค่าที่คำนวณได้'])tr.append(node('td',t));$('dailyTotal').replaceChildren(tr);}
function renderRaw(){if(!current)return;const labels={zero:'ศูนย์ทั้งคู่',value:'ข้อมูล',baseline:'ค่าเริ่มต้น',after_gap:'หลังช่วงศูนย์',decreased:'เลขสะสมลดลง'};$('rawTable').replaceChildren();for(const r of current.rows.filter(r=>r.date===$('rawDay').value)){const tr=node('tr');for(const t of [r.time,fmt(r.demand),fmt(r.energy),labels[r.status]])tr.append(node('td',t));$('rawTable').append(tr);}}
const NS='http://www.w3.org/2000/svg';
function svgNode(tag,attrs={},text){const n=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;return n;}
function base(id,max,label){const root=$(id);root.replaceChildren();const svg=svgNode('svg',{viewBox:'0 0 600 260',role:'img','aria-label':label});root.append(svg);for(let i=0;i<=4;i++){const y=20+i*48;svg.append(svgNode('line',{x1:58,y1:y,x2:584,y2:y,stroke:'#edf0f3'}));svg.append(svgNode('text',{x:48,y:y+4,'text-anchor':'end',fill:'#939ba5','font-size':11},fmt(max*(4-i)/4)));}return svg;}
function renderCharts(v){const active=v.rows.filter(r=>!r.zero);if(!active.length){for(const id of ['demandChart','energyChart']){const e=node('div','ไม่มีข้อมูลในช่วงที่เลือก');e.className='empty';$(id).replaceChildren(e);}return;}
 const max=Math.max(1,...active.map(r=>r.demand))*1.1,svg=base('demandChart',max,`Load Profile ${v.meter}`),lo=v.rows[0].ts,hi=v.rows.at(-1).ts;let path='',previous=null;
 for(const r of v.rows){if(r.zero){previous=null;continue;}const x=58+(r.ts-lo)/Math.max(1,hi-lo)*526,y=212-r.demand/max*192;path+=`${previous?'L':'M'}${x.toFixed(2)},${y.toFixed(2)} `;previous=r;}
 svg.append(svgNode('path',{d:path,fill:'none',stroke:'#ed7b20','stroke-width':2,'stroke-linejoin':'round'}));
 for(let i=0;i<5;i++){const dt=new Date(lo+(hi-lo)*i/4);svg.append(svgNode('text',{x:58+526*i/4,y:243,'text-anchor':i===0?'start':i===4?'end':'middle',fill:'#939ba5','font-size':11},v.days.length===1?dt.toISOString().slice(11,16):dt.toISOString().slice(8,10)+'/'+dt.toISOString().slice(5,7)));}
 const ymax=Math.max(1,...v.days.map(d=>d.energy.slice(0,3).reduce((s,x)=>s+(x??0),0)))*1.1,bars=base('energyChart',ymax,'พลังงานรายวันแยก TOU'),w=526/Math.max(1,v.days.length);
 v.days.forEach((d,j)=>{let bottom=212;d.energy.slice(0,3).forEach((value,i)=>{if(value===null)return;const h=value/ymax*192,rect=svgNode('rect',{x:58+j*w+2,y:bottom-h,width:Math.max(1,w-4),height:h,rx:2,fill:['#667d92','#ed7b20','#89b49e'][i]});rect.append(svgNode('title',{},`${d.date} · ${['OffPeak','OnPeak','Holiday'][i]} ${fmt(value)} kWh`));bars.append(rect);bottom-=h;});if(d.energy.slice(0,3).some(x=>x===null)){const mark=svgNode('text',{x:58+j*w+w/2,y:228,'text-anchor':'middle',fill:'#a67b40','font-size':10},'·');mark.append(svgNode('title',{},'ข้อมูลแยกช่วงไม่ครบ'));bars.append(mark);}if(j%Math.max(1,Math.ceil(v.days.length/7))===0)bars.append(svgNode('text',{x:58+j*w+w/2,y:249,'text-anchor':'middle',fill:'#939ba5','font-size':11},d.date.slice(8)));});
}
function renderComparison(period){
 const c=energyComparison(datasets.values(),period.key);$('comparisonPeriod').textContent=period.label;$('pieChart').replaceChildren();$('pieLegend').replaceChildren();
 if(c.available){
  const svg=svgNode('svg',{viewBox:'0 0 280 240',role:'img','aria-label':c.items.map(i=>`${i.label} ${fmt(i.percent)}% · ${fmt(i.energy)} kWh`).join(',')}),radius=86,circ=2*Math.PI*radius;let offset=0;
  svg.append(svgNode('circle',{cx:140,cy:120,r:radius,fill:'none',stroke:'#f0f2f4','stroke-width':32}));
  for(const i of c.items){const length=circ*i.percent/100,arc=svgNode('circle',{cx:140,cy:120,r:radius,fill:'none',stroke:i.color,'stroke-width':32,'stroke-dasharray':`${length} ${circ-length}`,'stroke-dashoffset':-offset,transform:'rotate(-90 140 120)'});arc.append(svgNode('title',{},`${i.label} ${i.percent.toFixed(1)}% · ${fmt(i.energy)} kWh`));svg.append(arc);offset+=length;}
  svg.append(svgNode('text',{x:140,y:104,'text-anchor':'middle',fill:'#7d8793','font-size':12},'รวมสองมิเตอร์'));
  svg.append(svgNode('text',{x:140,y:133,'text-anchor':'middle',fill:'#1c2530','font-size':26,'font-weight':650},fmt(c.total)));
  svg.append(svgNode('text',{x:140,y:154,'text-anchor':'middle',fill:'#7d8793','font-size':12},'kWh'));$('pieChart').append(svg);
 }else {const empty=node('div','ยังเปรียบเทียบไม่ได้');empty.className='empty';$('pieChart').append(empty);}
 for(const i of c.items){const row=node('div');row.className='pie-item';const name=node('span',i.label),dot=node('i');dot.style.background=i.color;name.prepend(dot);const percent=node('strong',i.percent===null?'—':i.percent.toFixed(1)+'%'),value=node('span',fmt(i.energy)+' kWh');value.className='pie-kwh';row.append(name,percent,value);$('pieLegend').append(row);}
 const sameEnd=c.items[0].lastReading===c.items[1].lastReading;
 $('comparisonNote').textContent=c.available?`สัดส่วนจากพลังงานรวมสองมิเตอร์ของเดือนนี้ ไม่ใช่สัดส่วนการใช้ไฟสุทธิของไซต์ · ${sameEnd?'ข้อมูลถึง '+c.items[0].lastReading:c.items.map(i=>i.label+' ถึง '+i.lastReading).join(' / ')} · คำนวณจากค่าที่อ่านได้ตามสูตร TOU เดิม`:'ต้องมีข้อมูลทั้งสองมิเตอร์ในเดือนเดียวกัน และมีพลังงานรวมมากกว่าศูนย์ จึงจะแสดงสัดส่วนได้';
}
function download(bytes,type,name){const url=URL.createObjectURL(new Blob([bytes],{type})),a=node('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('dailyExport').onclick=()=>{if(!current)return;const entries=[['Meter','Date','OffPeak kWh','OnPeak kWh','Holiday kWh','Total kWh','MD OffPeak kW','MD OnPeak kW','MD Holiday kW','Status'],...current.days.map(d=>[current.meter,d.date,...d.energy,...d.demand,d.status]),[current.meter,'TOTAL',...current.total.energy,...current.total.demand,'รวมเฉพาะค่าที่คำนวณได้']];download('\ufeff'+entries.map(r=>r.map(x=>'"'+String(x??'').replaceAll('"','""')+'"').join(',')).join('\r\n'),'text/csv;charset=utf-8',current.meter+'_TOU.csv');};
$('export').onclick=()=>{if(current)download(rawExcel(current.rows),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',current.meter+'_TOU.xlsx');};
$('meterMEA').onclick=()=>{selectedMeter='D01';options();};$('meterSolar').onclick=()=>{selectedMeter='D02';options();};$('period').onchange=render;$('rawDay').onchange=renderRaw;$('loadSamples').onclick=loadSamples;$('refreshFiles').onclick=loadSamples;
$('files').onchange=async e=>{const errors=[];for(const file of e.target.files){try{importFile(await file.arrayBuffer(),file.name);}catch(error){errors.push(file.name+': '+error.message);}}options();$('message').textContent=errors.join('\n');e.target.value='';};
if(online){
 $('onlineAccess').hidden=publicRead;$('viewToken').value=viewToken;$('siteCode').value=site;
 document.querySelector('.badge').textContent='ข้อมูลจริง · ออนไลน์';document.querySelector('footer').textContent=window.EMS_API_PHP?'GRAND DIGITAL · TOU บน Hosting บริษัท':'GRAND DIGITAL · TOU บน Cloudflare';
 document.querySelector('a[href^="/reports/"]').hidden=true;
 $('accessForm').onsubmit=e=>{e.preventDefault();if(loadingFiles)return;viewToken=$('viewToken').value.trim();site=$('siteCode').value.trim();sessionStorage.setItem('ems-view-token',viewToken);sessionStorage.setItem('ems-site',site);datasets.clear();folderFiles.clear();current=null;options();for(const id of ['energy','peak','latestTime','latestDate','energyHint','peakAt','coverage','comparisonNote','comparisonPeriod','chartMeter','fileCount'])$(id).textContent='—';$('periodText').textContent='กำลังเปิดข้อมูลไซต์ '+site;for(const id of ['demandChart','energyChart','pieChart','pieLegend','dailyTable','dailyTotal','rawTable','rawDay','auditSummary'])$(id).replaceChildren();$('export').disabled=true;$('dailyExport').disabled=true;loadSamples();};
 $('logout').onclick=()=>{sessionStorage.removeItem('ems-view-token');sessionStorage.removeItem('ems-site');location.reload();};
}
loadSamples();
