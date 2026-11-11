import test from 'node:test';
import assert from 'node:assert/strict';
import {periodsForMeter,datasetForSelection,energyComparison} from '../dashboard/selection.mjs';
const make=(device,key,energy)=>({name:device+key+'.tou',period:{device,key},rows:[{name:device+key+'.tou',index:0,date:key+'-01',time:'00:00',energy:100,demand:1,zero:false},{name:device+key+'.tou',index:1,date:key+'-01',time:'00:15',energy:100,demand:1,zero:false},{name:device+key+'.tou',index:2,date:key+'-01',time:'00:30',energy:100+energy,demand:1,zero:false}],sourceBuffer:new ArrayBuffer(112),outside:0,updated:key+'-01 00:00:00'});
const fixtures=[make('D01','2026-10',75),make('D02','2026-10',25),make('D01','2026-09',20)];
test('month choices use selected meter and sort newest first',()=>{assert.deepEqual(periodsForMeter(fixtures,'D01').map(p=>p.key),['2026-10','2026-09']);assert.equal(datasetForSelection(fixtures,'D02','2026-09'),undefined);});
test('comparison uses both meters in the same selected month, including iterator inputs',()=>{const c=energyComparison(fixtures.values(),'2026-10');assert.equal(c.available,true);assert.equal(c.total,100);assert.deepEqual(c.items.map(i=>i.percent),[75,25]);});
test('missing meter is not treated as zero percent',()=>{const c=energyComparison(fixtures,'2026-09');assert.equal(c.available,false);assert.equal(c.items[1].energy,null);});
test('all-zero comparison has no invented shares',()=>{assert.equal(energyComparison([make('D01','2026-10',0),make('D02','2026-10',0)],'2026-10').available,false);});
