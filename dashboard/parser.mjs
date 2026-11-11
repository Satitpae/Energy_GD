export function periodFromFilename(name) {
  const match=/^(.+)(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{2})\.tou$/i.exec(name);
  if(!match)throw Error('ชื่อไฟล์ต้องลงท้ายด้วยเดือนและปี เช่น DeviceSep26.tou');
  const month=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'].indexOf(match[2].toLowerCase())+1;
  const year=2000+Number(match[3]),key=`${year}-${String(month).padStart(2,'0')}`;
  return {year,month,key,device:match[1],start:key+'-01',end:key+'-'+new Date(Date.UTC(year,month,0)).getUTCDate(),
    label:new Date(Date.UTC(year,month-1,1)).toLocaleDateString('th-TH',{month:'long',year:'numeric',calendar:'gregory',timeZone:'UTC'})};
}
export function parseTou(buffer, name) {
  const period=periodFromFilename(name);
  const view = new DataView(buffer), bytes = new Uint8Array(buffer);
  const text = (a,b) => new TextDecoder('ascii').decode(bytes.slice(a,b));
  if (buffer.byteLength < 64 || text(0,8) !== 'TOUReg\0\0') throw Error('ไม่ใช่ไฟล์ TOUReg ที่รองรับ');
  if (view.getUint16(8,true) !== 64 || (buffer.byteLength-64)%16) throw Error('ขนาด header หรือแถวข้อมูลไม่ถูกต้อง');
  const date = text(10,28), m = /^(\d{2})\/(\d{2})\/(\d{4})(\d{2}):(\d{2}):(\d{2})$/.exec(date);
  if (!m) throw Error('อ่านวันที่ใน header ไม่ได้');
  const headerYear=+m[3], headerMonth=+m[2], day=+m[1];
  const check=new Date(Date.UTC(headerYear,headerMonth-1,day));
  if (headerMonth<1 || headerMonth>12 || check.getUTCDate()!==day || +m[4]>23 || +m[5]>59 || +m[6]>59) throw Error('วันที่ใน header ไม่ถูกต้อง');
  const {year,month}=period;
  const start=Date.UTC(year,month-1,1), rows=[], allRows=[];
  let previous=null, outside=0;
  for(let i=0;i<(buffer.byteLength-64)/16;i++) {
    const demand=view.getFloat64(64+i*16,true), energy=view.getFloat64(72+i*16,true);
    if (!Number.isFinite(demand)||!Number.isFinite(energy)) throw Error(`ตัวเลขไม่ถูกต้องในแถว ${i+1}`);
    const dt=new Date(start+i*900000), zero=demand===0&&energy===0;
    let status=zero?'zero':'value', delta=null;
    if (!zero) {
      if (previous && !previous.zero) {if(energy>=previous.energy) delta=energy-previous.energy; else status='decreased';}
      else status=previous?'after_gap':'baseline';
    }
    const row={name,index:i,ts:dt.getTime(),date:dt.toISOString().slice(0,10),day:dt.getUTCDate().toString().padStart(2,'0'),time:dt.toISOString().slice(11,16),demand,energy,delta,status,zero};
    allRows.push(row);
    if(dt.getUTCMonth()===month-1) rows.push(row); else outside++;
    previous=row;
  }
  return {name,period,sourceBuffer:buffer.slice(0),updated:`${m[3]}-${m[2]}-${m[1]} ${m[4]}:${m[5]}:${m[6]}`,rows,allRows,outside};
}

