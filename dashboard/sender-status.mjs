export function senderStatusView(meta,elapsedSeconds=0){
 if(!meta)return {state:'unavailable',label:'ตรวจสอบการเชื่อมต่อไม่ได้',timestamp:'—'};
 if(meta.last_seen_at===null)return {state:'unknown',label:'ยังไม่เคยได้รับการติดต่อ',timestamp:'—'};
 const seen=Date.parse(meta.last_seen_at),server=Date.parse(meta.server_time);
 if(!Number.isFinite(seen)||!Number.isFinite(server))return {state:'unavailable',label:'ตรวจสอบการเชื่อมต่อไม่ได้',timestamp:'—'};
 const age=Math.max(0,(server-seen)/1000+elapsedSeconds),stale=age>(meta.stale_after_seconds??180);
 const timestamp=new Intl.DateTimeFormat('th-TH',{year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23',calendar:'gregory',timeZone:'Asia/Bangkok'}).format(seen);
 return {state:stale?'stale':'connected',label:stale?'ไม่ได้รับการติดต่อเกิน 3 นาที':'ติดต่อได้',timestamp,age};
}
