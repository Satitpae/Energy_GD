import {readFile,writeFile,mkdir,readdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {parseTou} from '../dashboard/parser.mjs';
import {dailyTou,totalTou} from '../dashboard/tou.mjs';
import {auditDataset} from '../dashboard/trial.mjs';
const audits=[];
const files=(await readdir(new URL('../TOU File for test/',import.meta.url),{withFileTypes:true})).filter(f=>f.isFile()&&/^D0[12](Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d{2}\.tou$/i.test(f.name)).map(f=>f.name).sort();
for(const name of files){
 const bytes=await readFile(new URL('../TOU File for test/'+name,import.meta.url));
 const data=parseTou(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),name);
 const days=dailyTou(data,{firstDayQuarter:true,boundaries:'report'});
 audits.push({...auditDataset(data),sha256:createHash('sha256').update(bytes).digest('hex'),totals:totalTou(days),days});
}
await mkdir(new URL('../reports/',import.meta.url),{recursive:true});
await writeFile(new URL('../reports/audit.json',import.meta.url),JSON.stringify(audits,null,2));
const fmt=n=>n===null?'—':n.toLocaleString('en-US',{maximumFractionDigits:3});
let md='# ผลตรวจไฟล์ TOU ทุกเดือนในโฟลเดอร์\n\n';
md+='อ่านด้วย parser.mjs และ tou.mjs จาก Satitpae/Dashboard_TOU โดยไม่แก้สูตร รายละเอียดเวอร์ชันอยู่ใน SOURCE.json\n\n';
md+='เวลาทั้งหมดเป็นเวลาหน้าปัดหน้างานที่อนุมานจากลำดับแถว ไม่แปลงเขตเวลา วันที่ใน header เป็นวันที่เริ่มข้อมูล ไม่ใช่เวลาปรับปรุงล่าสุด\n\n';
for(const a of audits){
 md+=`## ${a.meter} — ${a.name}\n\n`;
 md+=`- ขนาด ${a.bytes} ไบต์; ${a.totalRows} แถว; ในเดือน ${a.monthRows} แถว; นอกเดือน ${a.outsideMonth} แถว (มีค่าจริง ${a.outsideNonzero} แถว)\n`;
 md+=`- Header: ${a.headerDate}; เดือนตรงชื่อไฟล์: ${a.headerMatchesFilename}\n- ข้อมูลจริง: ${a.firstReading} ถึง ${a.lastReading}\n`;
 md+=`- ศูนย์ท้ายไฟล์ ${a.trailingZeroRows} แถว; ศูนย์ทั้งคู่ภายในช่วงข้อมูล ${a.internalZeroRows} แถว; Energy เป็นศูนย์แต่มี Demand ${a.energyZeroWithDemand} แถว; ค่าติดลบ ${a.negativeReadings} แถว\n`;
 md+=`- ตัวอ่านเดิมติดสถานะเลขสะสมลดลง ${a.registerDecreases.length} แถว (รวมค่า Energy ศูนย์); เลขสะสมที่ไม่ใช่ศูนย์ลดลงจริง ${a.nonzeroRegisterDecreases.length} ครั้ง\n`;
 md+=`- Energy ตามสูตรเดิม: ${a.totals.energy.map(fmt).join(' / ')} kWh (OffPeak / OnPeak / Holiday / Total)\n`;
 md+=`- Maximum Demand: ${a.totals.demand.map(fmt).join(' / ')} kW (OffPeak / OnPeak / Holiday)\n- Demand สูงสุดทั้งช่วง: ${fmt(a.peakDemand)} kW ณ ${a.peakAt}\n\n`;
 if(a.internalZeroRanges.length)md+='ช่วงศูนย์ภายใน:\n\n'+a.internalZeroRanges.map(g=>`- ${g.from} ถึง ${g.to}: ${g.rows} แถว`).join('\n')+'\n\n';
}
md+='## วิธีคำนวณและข้อจำกัด\n\n- รูปแบบ TOUReg, header 64 ไบต์, คู่ float64 little-endian, ทุก 15 นาที\n- วันที่อิงท้ายชื่อไฟล์ แถวเลยเดือนเก็บไว้สำหรับอ่านขอบเวลา แต่ไม่แสดงเป็นวันที่ในเดือน\n- Energy วันแรกเริ่ม 00:15 วันอื่นเริ่ม 00:00; OnPeak ใช้ขอบ 09:00–22:00; วันสุดท้ายใช้เลขสะสมล่าสุด\n- Maximum Demand ใช้ Demand โดยตรง รวมขอบ 09:00 และ 22:00 ในทั้งสองช่วงตามต้นฉบับ\n- ศูนย์ทั้งคู่ระบุเป็นแถวว่าง/ศูนย์ ไม่สรุปว่าเป็นไฟดับ; หลังข้อมูลล่าสุดถือเป็นส่วนที่ยังไม่มีข้อมูล\n- ศูนย์ที่ขอบหรือเลขสะสมลดลงทำให้คำนวณ Energy ช่วงนั้นไม่ได้; ศูนย์ภายในอาจยังคำนวณ Energy จากขอบได้ แต่ Demand อาจไม่ครบ\n- ยอด OffPeak + OnPeak + Holiday อาจไม่เท่ากับ Total เพราะสูตรเดิมรวมแต่ละคอลัมน์เฉพาะวันที่คำนวณได้ และ Total บางวันยังคำนวณได้เมื่อขอบย่อยหายไป ห้ามตีความช่อง — ว่าเป็นศูนย์\n- เมื่อเลือกทุกจุดวัด การ์ด Energy เป็นผลบวกของสองมิเตอร์ ไม่ใช่ยอดใช้ไฟสุทธิของไซต์ และไม่ใช่ผลประหยัดจาก Solar\n- ใช้ปฏิทิน PEA 2026 จากโค้ดเดิม ซึ่งต้องเทียบปฏิทินและรายงาน MEA ก่อนใช้เรียกเก็บเงินจริง\n- Solar Cell แสดงตามหน่วยและสูตรเดิม ยังไม่ได้ยืนยัน CT/PT ทิศทางพลังงาน หรือสูตรประหยัดค่าไฟ\n- เป็นการตรวจโครงสร้างและเทียบโค้ด ยังไม่ได้เทียบกับรายงาน billing จริงจากหน้างาน\n';
await writeFile(new URL('../reports/ผลตรวจ-TOU.md',import.meta.url),md);
console.log(JSON.stringify(audits.map(({days,...a})=>a),null,2));
