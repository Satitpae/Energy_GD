// Parser timestamps represent local Thai clock values on a UTC-shaped axis.
export function recordedDemandRows(rows,now=Date.now()){
 const thaiNow=now+7*3600000,cutoff=Math.floor(thaiNow/900000)*900000,today=new Date(thaiNow).toISOString().slice(0,10);
 const latest=rows.filter(r=>!r.zero&&r.ts<cutoff).at(-1);
 return rows.map(r=>({...r,plotPending:r.ts>=cutoff||(r===latest&&r.date===today&&r.demand===0)}));
}
