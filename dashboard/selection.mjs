import {dailyTou,totalTou} from './tou.mjs';
export function datasetForSelection(datasets,meter,period){return [...datasets].find(d=>d.period.device.toUpperCase()===meter&&d.period.key===period);}
export function periodsForMeter(datasets,meter){return [...new Map([...datasets].filter(d=>d.period.device.toUpperCase()===meter).map(d=>[d.period.key,d.period])).values()].sort((a,b)=>b.key.localeCompare(a.key));}
export function energyComparison(datasets,period){
 const entries=[...datasets];
 const items=[['D01','MEA','#ed7b20'],['D02','Solar Cell','#4b9d83']].map(([meter,label,color])=>{
  const d=datasetForSelection(entries,meter,period),last=(d?.allRows??d?.rows??[]).findLast(r=>!r.zero);
  return {meter,label,color,energy:d?totalTou(dailyTou(d)).energy[3]:null,lastReading:last?last.date+' '+last.time:null};
 });
 const total=items.reduce((s,i)=>s+(i.energy??0),0),available=items.every(i=>i.energy!==null&&i.energy>=0)&&total>0;
 return {items:items.map(i=>({...i,percent:available?i.energy/total*100:null})),total,available};
}
