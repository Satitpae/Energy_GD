// PEA's published Off-Peak calendar for 2569 / 2026.
export const CALENDAR_SOURCE='https://www.pea.co.th/sites/default/files/users/user36/Off-Peak_Calendar_2569_0.jpg';
export const HOLIDAYS_2026=new Set(['01-01','03-03','04-06','04-13','04-14','04-15','05-01','05-04','05-31','06-03','07-28','07-29','07-30','08-12','10-13','10-23','12-05','12-10','12-31'].map(d=>'2026-'+d));
export function isHoliday(date,extra=new Set()) {
  const weekday=new Date(date+'T00:00:00Z').getUTCDay();
  return weekday===0 || weekday===6 || HOLIDAYS_2026.has(date) || extra.has(date);
}
export function dailyTou(dataset,{extra=new Set(),firstDayQuarter=true,boundaries='report'}={}) {
  const rows=dataset.allRows || dataset.rows, days=[...new Set(dataset.rows.map(r=>r.date))];
  const lastEnergy=rows.reduce((last,r,i)=>r.energy!==0?i:last,-1);
  return days.map((date,dayIndex)=>{
    const s=dayIndex*96, holiday=isHoliday(date,extra);
    const end=Math.min(96,lastEnergy-s),partial=end>=0&&end<96;
    const w=rows.slice(s,s+Math.max(0,end+1));
    const diff=(a,b)=>{
      const left=rows[s+a],right=rows[s+b];
      if(!left||!right||left.energy===0||right.energy===0||right.energy<left.energy)return null;
      // Never accept a register reset inside a segment, even if its final reading recovered.
      let prev=null;
      for(const r of rows.slice(s+a,s+b+1))if(r.energy!==0){if(prev!==null&&r.energy<prev)return null;prev=r.energy;}
      return right.energy-left.energy;
    };
    const max=(part)=>{const valid=part.filter(r=>!r.zero);return valid.length?Math.max(...valid.map(r=>r.demand)):null;};
    const start=dayIndex===0&&firstDayQuarter?1:0;
    const total=end>=start?diff(start,end):null;
    const on=holiday?0:end<0?null:end<=36?0:diff(36,Math.min(88,end));
    const morning=holiday?0:end>=start?diff(start,Math.min(36,end)):null;
    const night=holiday?0:end<0?null:end<=88?0:diff(88,end);
    const off=holiday?0:morning===null||night===null?null:morning+night;
    const dOff=holiday?0:max(boundaries==='report'?[...w.slice(0,37),...w.slice(88)]:[...w.slice(0,36),...w.slice(88,96)]);
    const dOn=holiday?0:max(w.slice(36,boundaries==='report'?89:88));
    const dHoliday=holiday?max(w.slice(0,boundaries==='report'?97:96)):0;
    const gaps=w.filter(r=>r.energy===0).length,any=w.slice(0,96).some(r=>!r.zero);
    return {name:dataset.name,date,holiday,energy:[off,on,holiday?total:0,total],demand:[dOff,dOn,dHoliday],
      gaps,status:!any?'ไม่มีข้อมูล':total===null||off===null||on===null?'ข้อมูลไม่ครบ':partial?`ข้อมูลถึง ${rows[s+end].time}`:gaps?'Energy ครบขอบเวลา / Demand อาจไม่ครบ':'ครบขอบเวลา',
      calendarKnown:date.startsWith('2026-'),startAt:start===1?'00:15':'00:00',endAt:end>=0?rows[s+end]?.time:null,partial};
  });
}
export function totalTou(days) {
  return {energy:[0,1,2,3].map(i=>days.some(d=>d.energy[i]!==null)?days.reduce((s,d)=>s+(d.energy[i]??0),0):null),
    demand:[0,1,2].map(i=>days.some(d=>d.demand[i]!==null)?Math.max(...days.map(d=>d.demand[i]??-Infinity)):null),
    incomplete:days.filter(d=>d.status!=='ครบขอบเวลา').length};
}

