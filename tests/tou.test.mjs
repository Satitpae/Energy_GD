import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {parseTou} from '../dashboard/parser.mjs';
import {dailyTou,totalTou} from '../dashboard/tou.mjs';
import {meterLabel,auditDataset} from '../dashboard/trial.mjs';

test('meter names follow confirmed mapping',()=>{
  assert.equal(meterLabel('D01Oct26.tou'),'MEA');
  assert.equal(meterLabel('D02Oct26.tou'),'Solar Cell');
  assert.equal(meterLabel('D03Oct26.tou'),'D03');
});
for(const name of ['D01Oct26.tou','D02Oct26.tou'])test(name+' real binary structure and time axis',async()=>{
 const b=await readFile(new URL('../TOU File for test/'+name,import.meta.url));
 const d=parseTou(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),name);
 assert.equal(d.period.key,'2026-10');assert.equal(d.allRows.length,3072);
 assert.equal(d.rows.length,2976);assert.equal(d.outside,96);
 assert.equal(d.rows[0].date,'2026-10-01');assert.equal(d.rows[0].time,'00:00');
 assert.equal(d.rows.at(-1).date,'2026-10-31');assert.equal(d.rows.at(-1).time,'23:45');
 const audit=auditDataset(d);assert.equal(audit.headerMatchesFilename,true);
 assert.ok(audit.lastReading);assert.ok(audit.trailingZeroRows>0);
 assert.equal(dailyTou(d).length,31);
});
function fixture(){const rows=Array.from({length:193},(_,index)=>{const dt=new Date(Date.UTC(2026,9,1)+index*900000);return {name:'D01Oct26.tou',index,date:dt.toISOString().slice(0,10),time:dt.toISOString().slice(11,16),energy:1000+index*10,demand:index,zero:false};});return {name:'D01Oct26.tou',allRows:rows,rows:rows.slice(0,192)};}
test('original first-day quarter and inclusive demand boundaries retained',()=>{
 const days=dailyTou(fixture());
 assert.deepEqual(days[0].energy,[430,520,0,950]);
 assert.deepEqual(days[0].demand,[96,88,0]);
 assert.equal(days[1].energy[3],960);
 assert.equal(totalTou(days).energy[3],1910);
});
test('register reset invalidates segment even after recovery',()=>{
 const d=fixture();d.allRows[40].energy=1;
 assert.equal(dailyTou(d)[0].energy[1],null);
 assert.equal(dailyTou(d)[0].energy[3],null);
});
test('zero boundaries are not treated as valid energy',()=>{
 const d=fixture();d.allRows[36].energy=0;
 assert.equal(dailyTou(d)[0].energy[0],null);
 assert.equal(dailyTou(d)[0].energy[1],null);
});
test('weekends and original October holidays use holiday column',()=>{
 const d=fixture();d.rows=d.rows.slice(0,96);d.rows.forEach(r=>r.date='2026-10-13');
 const day=dailyTou(d)[0];assert.equal(day.holiday,true);assert.deepEqual(day.energy,[0,0,950,950]);
});
test('rejects invalid signature and truncated pair',()=>{
 assert.throws(()=>parseTou(new ArrayBuffer(64),'D01Oct26.tou'));
 const b=new ArrayBuffer(65);new Uint8Array(b).set(new TextEncoder().encode('TOUReg\0\0'));new DataView(b).setUint16(8,64,true);
 assert.throws(()=>parseTou(b,'D01Oct26.tou'),/header/);
});
