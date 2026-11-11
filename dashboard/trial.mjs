export function meterLabel(name) {
  const device=/^(.+?)(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d{2}\.tou$/i.exec(name)?.[1]??name;
  return ({D01:'MEA',D02:'Solar Cell'})[device.toUpperCase()]??device;
}
export function auditDataset(dataset) {
  const rows=dataset.allRows;
  const active=rows.filter(r=>!r.zero);
  const last=active.at(-1);
  const lastIndex=last?.index??-1;
  const inside=rows.slice(0,lastIndex+1);
  const internalZeroRanges=[];
  for(let i=0;i<inside.length;i++)if(inside[i].zero){
    const first=i;while(i+1<inside.length&&inside[i+1].zero)i++;
    internalZeroRanges.push({from:inside[first].date+' '+inside[first].time,to:inside[i].date+' '+inside[i].time,rows:i-first+1});
  }
  const stamp=r=>r?r.date+' '+r.time:null;
  const peak=active.reduce((best,r)=>!best||r.demand>best.demand?r:best,null);
  return {name:dataset.name,meter:meterLabel(dataset.name),period:dataset.period.key,
    headerDate:dataset.updated,headerMatchesFilename:dataset.updated.slice(0,7)===dataset.period.key,
    bytes:dataset.sourceBuffer.byteLength,totalRows:rows.length,monthRows:dataset.rows.length,outsideMonth:dataset.outside,
    firstReading:stamp(active[0]),lastReading:stamp(last),lastEnergy: last?.energy??null,
    trailingZeroRows:rows.length-lastIndex-1,internalZeroRows:inside.filter(r=>r.zero).length,internalZeroRanges,
    energyZeroWithDemand:inside.filter(r=>r.energy===0&&!r.zero).length,
    registerDecreases:rows.filter(r=>r.status==='decreased').map(r=>({at:stamp(r),energy:r.energy})),
    nonzeroRegisterDecreases:inside.filter((r,i)=>r.energy!==0&&inside.slice(0,i).findLast(p=>p.energy!==0)?.energy>r.energy).map(r=>({at:stamp(r),energy:r.energy})),
    negativeReadings:rows.filter(r=>r.demand<0||r.energy<0).length,
    peakDemand:peak?.demand??null,peakAt:stamp(peak),
    outsideNonzero:rows.filter(r=>r.date.slice(0,7)!==dataset.period.key&&!r.zero).length};
}
