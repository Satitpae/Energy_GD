import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {parseTou} from '../dashboard/parser.mjs';
import {summarizePeriod,availableYears,availableMonths} from '../dashboard/combined.mjs';
async function data(name){const b=await readFile(new URL('../TOU File for test/'+name,import.meta.url));return parseTou(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),name);}
test('monthly and annual summaries keep two meters separate and missing months null',async()=>{
 const entries=await Promise.all(['D01Sep26.tou','D02Sep26.tou','D01Oct26.tou','D02Oct26.tou'].map(data));
 const month=summarizePeriod(entries,'2026-10');
 assert.deepEqual(month.items.map(i=>i.energy),[94623,92017]);
 const year=summarizePeriod(entries,'2026');
 assert.equal(year.months.length,12);
 assert.deepEqual(year.items.map(i=>i.energy),[111806+94623,110643+92017]);
 assert.deepEqual(year.items.map(i=>i.fileCount),[2,2]);
 assert.equal(year.months[0].items[0].energy,null);
 assert.equal(year.months[8].items[0].energy,111806);
 assert.ok(Math.abs(year.items[0].peak.demand-553.088)<1e-8);
 assert.equal(year.items[0].latest,'2026-10-26 10:15');
 assert.equal(year.available,true);
});
test('one meter and no data do not invent zero or percentages',async()=>{
 const d=await data('D01Oct26.tou');const s=summarizePeriod([d],'2026');
 assert.equal(s.items[1].energy,null);assert.equal(s.available,false);
 assert.equal(s.items[0].percent,null);assert.equal(s.items[1].fileCount,0);
 assert.equal(summarizePeriod([],'2025').items[0].energy,null);
});
test('valid zero consumption remains zero rather than missing',async()=>{
 const original=await data('D01Oct26.tou');
 const rows=original.rows.map(r=>({...r,energy:1000,zero:false}));
 const allRows=original.allRows.map(r=>({...r,energy:1000,zero:false}));
 const result=summarizePeriod([{...original,rows,allRows}],'2026');
 assert.equal(result.items[0].energy,0);
 assert.equal(result.months[9].items[0].energy,0);
 assert.equal(result.months[8].items[0].energy,null);
 assert.equal(result.items[0].fileCount,1);
});
test('year/month choices use union of both meters, sorted and year scoped',()=>{
 const files=['D01Oct26.tou','D02Sep26.tou','D01Dec25.tou','D02Oct26.tou'];
 assert.deepEqual(availableYears(files),['2026','2025']);
 assert.deepEqual(availableMonths(files,'2026'),['2026-10','2026-09']);
});
