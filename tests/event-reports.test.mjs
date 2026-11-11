import test from 'node:test';
import assert from 'node:assert/strict';
import {filterEvents, summarize, csv, calendarDays, groupSetpoints} from '../reports/advreports-events/core.mjs';
const rows = [
 {ID:'1',DataDateTime:'2024-11-01 08:00:00',EndDateTime:null,UserKey:'MDB24_off',Type:'0',Message:'Status Fail'},
 {ID:'2',DataDateTime:'2024-11-30 23:59:59',EndDateTime:'2024-12-01 01:00:00',UserKey:'MDB24_on',Type:'0',Message:'Status Success'},
 {ID:'3',DataDateTime:'2024-12-01 08:00:00',EndDateTime:null,UserKey:null,Type:'101',Message:'admin logged in.'}
];
test('date boundaries include full end day; devices and missing end remain independent',()=>{
 assert.deepEqual(filterEvents(rows,{from:'2024-11-01',to:'2024-11-30',device:'MDB24_off'}).map(r=>r.ID),['1']);
 assert.deepEqual(filterEvents(rows,{end:'missing',message:'Status Fail'}).map(r=>r.ID),['1']);
 assert.deepEqual(filterEvents(rows,{type:'101',search:'ADMIN'}).map(r=>r.ID),['3']);
 assert.equal(filterEvents(rows,{from:'2025-01-01'}).length,0);
});
test('daily setpoints group by Type and exact UserKey, without merging suffixes or unnamed rows',()=>{
 const groups=groupSetpoints([...rows,{...rows[0],ID:'4',Type:4},{...rows[0],ID:'5'}]);
 assert.equal(groups.length,2);
 assert.deepEqual(groups.find(g=>g.type==='0').setpoints.map(s=>[s.name,s.count]),[['MDB24_off',2],['MDB24_on',1]]);
 assert.equal(groups.find(g=>g.type==='4').setpoints[0].name,'MDB24_off');
});
test('summary distinguishes message counts from complete end times',()=>{
 assert.deepEqual(summarize(rows),{total:3,fail:1,success:1,communication:0,web:1,complete:1});
});
test('setpoint messages are separate from Communication Fail; numeric types work',()=>{
 const result=summarize([...rows,{Type:4,Message:'Communication Fail',EndDateTime:null},{Type:101,Message:'login',EndDateTime:null}]);
 assert.equal(result.communication,1);assert.equal(result.fail,1);assert.equal(result.success,1);assert.equal(result.web,2);
});
test('CSV preserves zero and quotes; neutralizes spreadsheet formulas',()=>{
 const text=csv([{ID:'0',UserKey:'=1+1',Message:'a,"b"',EndDateTime:null}]);
 assert.ok(text.includes('"0"'));assert.ok(text.includes('"\'=1+1"'));assert.ok(text.includes('"a,""b"""'));
});
test('calendar uses start date once per record and preserves empty days and month edges',()=>{
 const days=calendarDays(rows,'2024-11');
 assert.equal(days.length,30);assert.equal(days[0].weekday,5);
 assert.equal(days[0].total,1);assert.equal(days[1].total,0);
 assert.equal(days[29].total,1);assert.equal(days.reduce((n,d)=>n+d.total,0),2);
 assert.equal(calendarDays([], '2024-02').length,29);
 assert.equal(calendarDays([], '2026-02').length,28);
 assert.deepEqual(filterEvents(rows,{day:'2024-11-30'}).map(r=>r.ID),['2']);
});
test('calendar groups by Type even when different types have the same message',()=>{
 const day=calendarDays([
  {DataDateTime:'2026-10-29 12:00:00',Type:0,Message:'Communication Fail'},
  {DataDateTime:'2026-10-29 12:01:00',Type:4,Message:'Communication Fail'},
  {DataDateTime:'2026-10-29 12:02:00',Type:'4',Message:'other'},
 ],'2026-10')[28];
 assert.deepEqual(day.byType,{'0':1,'4':2});
 assert.equal(Object.values(day.byType).reduce((a,b)=>a+b,0),day.total);
});
