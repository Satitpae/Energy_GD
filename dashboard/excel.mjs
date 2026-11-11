// Browser-side XLSX exporter: four raw-data columns, one worksheet per meter.
// Uses standard OOXML parts in a ZIP (stored entries); no network or dependencies.
const enc=new TextEncoder();
const xml=s=>String(s).replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g,'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&apos;');
const pre='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>';
const ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main';
function crc32(bytes){let c=0xffffffff;for(const b of bytes){c^=b;for(let i=0;i<8;i++)c=(c>>>1)^((c&1)?0xedb88320:0);}return(c^0xffffffff)>>>0;}
function zip(files){
  const parts=[],central=[];let offset=0;
  for(const [name,content]of files){const n=enc.encode(name),data=enc.encode(content),crc=crc32(data);
    const header=new Uint8Array(30+n.length),v=new DataView(header.buffer);v.setUint32(0,0x04034b50,true);v.setUint16(4,20,true);v.setUint16(6,0x800,true);v.setUint16(12,33,true);v.setUint32(14,crc,true);v.setUint32(18,data.length,true);v.setUint32(22,data.length,true);v.setUint16(26,n.length,true);header.set(n,30);
    const dir=new Uint8Array(46+n.length),d=new DataView(dir.buffer);d.setUint32(0,0x02014b50,true);d.setUint16(4,20,true);d.setUint16(6,20,true);d.setUint16(8,0x800,true);d.setUint16(14,33,true);d.setUint32(16,crc,true);d.setUint32(20,data.length,true);d.setUint32(24,data.length,true);d.setUint16(28,n.length,true);d.setUint32(42,offset,true);dir.set(n,46);
    parts.push(header,data);central.push(dir);offset+=header.length+data.length;
  }
  const size=central.reduce((s,a)=>s+a.length,0),end=new Uint8Array(22),v=new DataView(end.buffer);v.setUint32(0,0x06054b50,true);v.setUint16(8,files.length,true);v.setUint16(10,files.length,true);v.setUint32(12,size,true);v.setUint32(16,offset,true);
  const output=new Uint8Array(offset+size+22);let cursor=0;for(const part of [...parts,...central,end]){output.set(part,cursor);cursor+=part.length;}return output;
}
function sheetNames(names){const used=new Set();return names.map(name=>{const base=name.replace(/\.tou$/i,'').replace(/[\\/?*\[\]:]/g,'_').replace(/^'+|'+$/g,'').slice(0,31)||'Meter';let value=base,i=1;while(used.has(value.toLowerCase())){const suffix=` (${++i})`;value=base.slice(0,31-suffix.length)+suffix;}used.add(value.toLowerCase());return value;});}
export function rawExcel(rows){
  if(!rows.length)throw Error('ไม่มีข้อมูลที่จะส่งออก');
  const groups=new Map();for(const row of rows){if(!groups.has(row.name))groups.set(row.name,[]);groups.get(row.name).push(row);}
  const names=sheetNames([...groups.keys()]),files=[];
  const ct='http://schemas.openxmlformats.org/package/2006/content-types';
  files.push(['[Content_Types].xml',pre+`<Types xmlns="${ct}"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>${names.map((_,i)=>`<Override PartName="/xl/worksheets/sheet${i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`).join('')}</Types>`]);
  const relns='http://schemas.openxmlformats.org/package/2006/relationships',officens='http://schemas.openxmlformats.org/officeDocument/2006/relationships';
  files.push(['_rels/.rels',pre+`<Relationships xmlns="${relns}"><Relationship Id="rId1" Type="${officens}/officeDocument" Target="xl/workbook.xml"/></Relationships>`]);
  files.push(['xl/workbook.xml',pre+`<workbook xmlns="${ns}" xmlns:r="${officens}"><sheets>${names.map((name,i)=>`<sheet name="${xml(name)}" sheetId="${i+1}" r:id="rId${i+1}"/>`).join('')}</sheets></workbook>`]);
  files.push(['xl/_rels/workbook.xml.rels',pre+`<Relationships xmlns="${relns}">${names.map((_,i)=>`<Relationship Id="rId${i+1}" Type="${officens}/worksheet" Target="worksheets/sheet${i+1}.xml"/>`).join('')}<Relationship Id="rId${names.length+1}" Type="${officens}/styles" Target="styles.xml"/></Relationships>`]);
  files.push(['xl/styles.xml',pre+`<styleSheet xmlns="${ns}"><numFmts count="2"><numFmt numFmtId="164" formatCode="hh:mm"/><numFmt numFmtId="165" formatCode="0.###############"/></numFmts><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FFECECEC"/><bgColor indexed="64"/></patternFill></fill></fills><borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border><border><left style="thin"><color rgb="FFCCCCCC"/></left><right style="thin"><color rgb="FFCCCCCC"/></right><top style="thin"><color rgb="FFCCCCCC"/></top><bottom style="thin"><color rgb="FFCCCCCC"/></bottom><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="4"><xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0"><alignment horizontal="left"/></xf><xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyAlignment="1"><alignment horizontal="center"/></xf><xf numFmtId="164" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1"><alignment horizontal="left"/></xf><xf numFmtId="165" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1"><alignment horizontal="left"/></xf></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>`]);
  let sheet=0;
  for(const group of groups.values()){
    let previousDate='',body='<row r="1" ht="24" customHeight="1">'+['Day','Time','Demand','Energy'].map((h,i)=>`<c r="${'ABCD'[i]}1" t="inlineStr" s="1"><is><t>${h}</t></is></c>`).join('')+'</row>';
    for(const [i,row]of group.entries()){const r=i+2,[hour,minute]=row.time.split(':').map(Number),day=row.date!==previousDate?row.day:'';
      if(!Number.isFinite(row.demand)||!Number.isFinite(row.energy))throw Error('ตัวเลขไม่ถูกต้อง');
      body+=`<row r="${r}" ht="20" customHeight="1"><c r="A${r}" t="inlineStr" s="0"><is><t>${xml(day)}</t></is></c><c r="B${r}" s="2"><v>${(hour*60+minute)/1440}</v></c><c r="C${r}" s="3"><v>${row.demand}</v></c><c r="D${r}" s="3"><v>${row.energy}</v></c></row>`;previousDate=row.date;
    }
    files.push([`xl/worksheets/sheet${++sheet}.xml`,pre+`<worksheet xmlns="${ns}"><dimension ref="A1:D${group.length+1}"/><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><sheetFormatPr defaultRowHeight="20"/><cols><col min="1" max="1" width="12" customWidth="1"/><col min="2" max="2" width="14" customWidth="1"/><col min="3" max="4" width="20" customWidth="1"/></cols><sheetData>${body}</sheetData></worksheet>`]);
  }
  return zip(files);
}

