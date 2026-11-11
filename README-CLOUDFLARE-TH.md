# TOU บน Cloudflare

## ขอบเขต

Pages project: `granddigital-ems-tou` ในบัญชี engineering@granddigital.co.th

R2 bucket ส่วนตัว: `granddigital-ems-tou-files` ผูกชื่อ `TOU_BUCKET` กับ Pages Functions ไฟล์เก็บเป็น `main/D01Oct26.tou` ฯลฯ ชื่อเดิมในไซต์เดียวกันแทนที่ฉบับเดิม ไม่เก็บประวัติแต่ละเวอร์ชัน

API `/api/tou-files` และ `/api/tou-file` ใช้โทเคนดูข้อมูล ส่วน `/api/upload` ใช้โทเคนส่งไฟล์แยกกัน จำกัด 128 KiB ต่อไฟล์ ตรวจด้วยตัวอ่าน TOU เดิมและเทียบวันที่เริ่มใน header กับชื่อไฟล์

## เตรียมและ deploy

1. `node tools/build-cloud.mjs` สร้าง `dist` ด้วยรายชื่อไฟล์ที่อนุญาต ไม่มีไฟล์ TOU รายงาน โทเคน หรือ config ตัวส่งอยู่ในชุดเว็บ
2. `node tools/prepare-cloud-secrets.mjs` สร้างโทเคนสุ่มสองชุดใน `.local/pages-secrets.json` และตั้งค่า uploader เฉพาะในเครื่อง ไม่พิมพ์ค่าโทเคนลง log
3. ใช้ Wrangler ที่ `tools/cloudflare/node_modules/wrangler/bin/wrangler.js` เข้าสู่ระบบด้วยสิทธิ์ Pages/Workers ที่ผู้ใช้อนุญาต
4. ตรวจ R2 เปิดใช้งานแล้ว สร้าง bucket และ Pages project ตามชื่อข้างต้น หากต้องยอมรับเงื่อนไขบริการหรือเพิ่มข้อมูลชำระเงิน ให้เจ้าของบัญชีทำขั้นตอนนั้น
5. ตั้ง Pages secrets `VIEW_TOKEN`, `UPLOAD_TOKEN` จากไฟล์ส่วนตัว แล้ว deploy เฉพาะ `dist` พร้อม Functions และ R2 binding ใน `wrangler.toml`
6. ยืนยัน API ปฏิเสธคำขอที่ไม่มีโทเคน ก่อนส่งไฟล์จริงขึ้นออนไลน์

ไม่แก้หรือ push repository เดิม ไม่ตั้ง public URL ของ R2 และไม่เปลี่ยนโดเมน

## เปิด Dashboard

เปิด URL หลัง deploy แล้วระบุไซต์ `main` และโทเคนดูข้อมูลจาก `.local/view-token.txt` โทเคนเก็บเฉพาะ session ของแท็บ เมื่อใช้เครื่องร่วมกันกด “ออกจากข้อมูล” เมื่อเสร็จ เลือก MEA / Solar Cell และเดือนข้อมูลได้ตามเดิม

## ตัวส่งไฟล์หน้างาน

ติดตั้ง Python 3 บนเครื่องหน้างาน แล้วคัดลอก `uploader` ไปยังเครื่องนั้น แก้ `config.local.json` ให้ `folder` ชี้โฟลเดอร์ TOU จริง โทเคนในไฟล์นี้เป็นโทเคนส่งข้อมูล ไม่ใช่โทเคน Cloudflare ของเจ้าของบัญชี

- ทดลองตรวจไฟล์โดยไม่ส่ง: `python uploader/send.py --config uploader/config.local.json --dry-run`
- ส่งหนึ่งรอบ: `python uploader/send.py --config uploader/config.local.json --once`
- ส่งต่อเนื่อง: เปิด `uploader/start-uploader.cmd` หรือรันโดยไม่ใส่ `--once`

ตรวจทุก 60 วินาที ใช้ SHA-256 ตรวจเนื้อหาใหม่/เปลี่ยน ยอมรับ HTTPS เท่านั้น ไม่ตาม redirect ของการอัปโหลด บันทึกสถานะแบบแทนที่ไฟล์เมื่อเซิร์ฟเวอร์ยืนยันสำเร็จ เมื่อส่งไม่สำเร็จจะลองใหม่รอบหน้า ห้ามเปิดตัวส่งซ้อนกันสองชุดด้วยไฟล์สถานะเดียวกัน

ตัวส่งจะไม่เริ่มทำงานเองหลังรีสตาร์ต Windows จนกว่าจะตั้ง Task Scheduler บนเครื่องหน้างาน การตั้งเริ่มอัตโนมัติและเส้นทางจริงหน้างานยังต้องทำบนเครื่องนั้น

## ข้อจำกัด

โทเคนใช้ร่วมกันในโปรเจกต์ ยังไม่มีบัญชีผู้ใช้รายบุคคล/สิทธิ์แยกไซต์ ปฏิทิน TOU เป็น PEA 2026 จากต้นฉบับ ยังต้องยืนยันกับรายงาน MEA ก่อนใช้ Billing ไม่มีการคิดค่าไฟ tariff ข้อมูลเป็นช่วง 15 นาที ไม่ใช่ Realtime ยังไม่ได้ติดตั้งบนเครื่องหน้างานจริงหรือทดสอบมือถือจริง
