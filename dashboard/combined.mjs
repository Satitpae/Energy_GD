import {periodFromFilename} from './parser.mjs';
import {dailyTou,totalTou} from './tou.mjs';
export const METERS=[{meter:'D01',label:'MEA',color:'#2463a6'},{meter:'D02',label:'Solar Cell',color:'#ed7b20'}];
function periods(names){return names.flatMap(name=>{try{const p=periodFromFilename(name);return /^D0[12]$/i.test(p.device)?[p]:[];}catch{return [];}});}
export function availableYears(names){return [...new Set(periods(names).map(p=>String(p.year)))].sort().reverse();}
export function availableMonths(names,year){return [...new Set(periods(names).filter(p=>String(p.year)===year).map(p=>p.key))].sort().reverse();}
function meterSummary(entries,meta){
 const selected=entries.filter(d=>d.period.device.toUpperCase()===meta.meter);let energy=null,peak=null,latest=null,daysWithEnergy=0;
 for(const d of selected){const days=dailyTou(d),value=totalTou(days).energy[3];if(value!==null)energy=(energy??0)+value;daysWithEnergy+=days.filter(day=>day.energy[3]!==null).length;
  for(const r of d.rows)if(!r.zero){if(!peak||r.demand>peak.demand)peak=r;const at=r.date+' '+r.time;if(!latest||at>latest)latest=at;}
 }
 return {...meta,energy,peak,latest,fileCount:selected.length,daysWithEnergy};
}
export function summarizePeriod(datasets,period){
 const entries=[...datasets].filter(d=>d.period.key.startsWith(period.length===4?period+'-':period));
 const items=METERS.map(meta=>meterSummary(entries,meta));const available=items.every(i=>i.energy!==null&&i.energy>=0)&&items.reduce((s,i)=>s+(i.energy??0),0)>0;
 const total=items.reduce((s,i)=>s+(i.energy??0),0);
 const months=period.length===4?Array.from({length:12},(_,i)=>{const key=period+'-'+String(i+1).padStart(2,'0');return {key,items:METERS.map(meta=>meterSummary(entries.filter(d=>d.period.key===key),meta))};}):[];
 return {items:items.map(i=>({...i,percent:available?i.energy/total*100:null})),months,total,available};
}
