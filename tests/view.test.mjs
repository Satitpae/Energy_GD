import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {parseTou} from '../dashboard/parser.mjs';
import {dashboardView} from '../dashboard/view.mjs';
for(const [name,energy,peak]of [['D01Oct26.tou',94623,553.088],['D02Oct26.tou',92017,474.734]])test(name+' summary keeps meters separate',async()=>{
 const b=await readFile(new URL('../TOU File for test/'+name,import.meta.url));const d=parseTou(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),name);
 const v=dashboardView(d,'2026-10-01','2026-10-31');
 assert.equal(v.total.energy[3],energy);assert.ok(Math.abs(v.peak.demand-peak)<1e-8);
 assert.equal(v.audit.lastReading,'2026-10-26 10:15');assert.equal(v.days.length,31);
 const day=dashboardView(d,'2026-10-26','2026-10-26');
 assert.equal(day.days.length,1);assert.equal(day.rows.length,96);assert.equal(day.days[0].endAt,'10:15');
 const empty=dashboardView(d,'2026-10-27','2026-10-31');assert.equal(empty.peak,null);assert.equal(empty.total.energy[3],null);
});
