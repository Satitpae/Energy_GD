import {dailyTou,totalTou} from './tou.mjs';
import {auditDataset,meterLabel} from './trial.mjs';
export function dashboardView(dataset,from,to){
 const within=r=>(!from||r.date>=from)&&(!to||r.date<=to);
 const rows=dataset.rows.filter(within),days=dailyTou(dataset,{firstDayQuarter:true,boundaries:'report'}).filter(within);
 const peak=rows.filter(r=>!r.zero).reduce((best,r)=>!best||r.demand>best.demand?r:best,null);
 return {name:dataset.name,meter:meterLabel(dataset.name),rows,days,peak,total:totalTou(days),audit:auditDataset(dataset)};
}
