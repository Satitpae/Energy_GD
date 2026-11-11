import {parseTou,periodFromFilename} from '../dashboard/parser.mjs';
const LIMIT=128*1024;
const headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'};
const json=(data,status=200)=>Response.json(data,{status,headers});
function fail(message,status=400){throw Object.assign(new Error(message),{status});}
async function sameToken(a,b){const digest=s=>crypto.subtle.digest('SHA-256',new TextEncoder().encode(s));const [x,y]=await Promise.all([digest(a),digest(b)]);const p=new Uint8Array(x),q=new Uint8Array(y);let diff=0;for(let i=0;i<p.length;i++)diff|=p[i]^q[i];return diff===0;}
function fileName(raw){if(!/^D0[12](Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d{2}\.tou$/i.test(raw??''))fail('ชื่อไฟล์ TOU ไม่ถูกต้อง');const p=periodFromFilename(raw);return p.device.toUpperCase()+['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][p.month-1]+String(p.year).slice(-2)+'.tou';}
async function boundedBody(request){const length=request.headers.get('Content-Length');if(length&&Number(length)>LIMIT)fail('ไฟล์เกิน 128 KiB',413);if(!request.body)fail('ไม่มีไฟล์');const reader=request.body.getReader(),parts=[];let size=0;while(true){const {value,done}=await reader.read();if(done)break;size+=value.length;if(size>LIMIT){await reader.cancel();fail('ไฟล์เกิน 128 KiB',413);}parts.push(value);}const out=new Uint8Array(size);let offset=0;for(const p of parts){out.set(p,offset);offset+=p.length;}return out.buffer;}
export async function handleApi(request,env){
 try{
  if(!env.VIEW_TOKEN||!env.UPLOAD_TOKEN||env.VIEW_TOKEN===env.UPLOAD_TOKEN||!env.TOU_BUCKET)return json({error:'ระบบยังตั้งค่าไม่ครบ'},503);
  const url=new URL(request.url),upload=url.pathname==='/api/upload';
  const token=request.headers.get('Authorization')?.match(/^Bearer (.+)$/)?.[1]??'';
  if(!token||!await sameToken(token,upload?env.UPLOAD_TOKEN:env.VIEW_TOKEN))return json({error:'กรุณาใช้โทเคนที่ถูกต้อง'},401);
  const site=url.searchParams.get('site')??'main';if(!/^[a-z0-9][a-z0-9_-]{0,47}$/.test(site))fail('ชื่อไซต์ไม่ถูกต้อง');
  if(url.pathname==='/api/tou-files'){
   if(request.method!=='GET')return json({error:'Method not allowed'},405);
   const files=[];let cursor;
   do{const page=await env.TOU_BUCKET.list({prefix:site+'/',cursor});for(const o of page.objects){const name=o.key.slice(site.length+1);if(/^D0[12](Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d{2}\.tou$/i.test(name))files.push({name,size:o.size});}cursor=page.truncated?page.cursor:undefined;}while(cursor);
   return json({site,files:files.sort((a,b)=>a.name.localeCompare(b.name))});
  }
  if(url.pathname==='/api/tou-file'){
   if(request.method!=='GET')return json({error:'Method not allowed'},405);
   const name=fileName(url.searchParams.get('name')),object=await env.TOU_BUCKET.get(site+'/'+name);
   return object?new Response(object.body,{headers:{...headers,'Content-Type':'application/octet-stream','Content-Disposition':`attachment; filename="${name}"`}}):json({error:'ไม่พบไฟล์'},404);
  }
  if(upload){
   if(request.method!=='POST')return json({error:'Method not allowed'},405);
   const name=fileName(url.searchParams.get('name')),buffer=await boundedBody(request);
   let data;try{data=parseTou(buffer,name);}catch(e){fail(e.message);}
   if(data.updated!==data.period.start+' 00:00:00')fail('วันที่เริ่มใน header ไม่ตรงกับเดือนในชื่อไฟล์');
   if(data.rows.length<2||!data.rows.some(r=>!r.zero))fail('ไม่มีข้อมูลในไฟล์');
   await env.TOU_BUCKET.put(site+'/'+name,buffer,{httpMetadata:{contentType:'application/octet-stream'}});
   return json({ok:true,site,name,size:buffer.byteLength});
  }
  return json({error:'Not found'},404);
 }catch(e){return json({error:e.status?e.message:'ระบบจัดเก็บไฟล์ขัดข้อง กรุณาลองใหม่'},e.status??500);}
}
