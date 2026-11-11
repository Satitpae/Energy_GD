import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {handleApi} from '../cloud/api.mjs';
const env=()=>({VIEW_TOKEN:'read-test-token',UPLOAD_TOKEN:'write-test-token',TOU_BUCKET:new Bucket()});
class Bucket{
 objects=new Map();
 async put(key,bytes){this.objects.set(key,new Uint8Array(bytes));}
 async get(key){const b=this.objects.get(key);return b?{body:b,size:b.length}:null;}
 async list({prefix,cursor}){const keys=[...this.objects.keys()].filter(k=>k.startsWith(prefix)).sort(),start=Number(cursor??0),slice=keys.slice(start,start+1);return {objects:slice.map(key=>({key,size:this.objects.get(key).length})),truncated:start+1<keys.length,cursor:String(start+1)};}
}
const req=(path,token,method='GET',body)=>new Request('https://ems.example'+path,{method,headers:token?{Authorization:'Bearer '+token}:{},body});
const fixture=()=>readFile(new URL('../TOU File for test/D01Oct26.tou',import.meta.url));
test('anonymous denied and read/upload tokens cannot be interchanged',async()=>{const e=env();for(const path of ['/api/tou-files','/api/tou-file?name=D01Oct26.tou'])assert.equal((await handleApi(req(path),e)).status,401);assert.equal((await handleApi(req('/api/tou-files',e.UPLOAD_TOKEN),e)).status,401);assert.equal((await handleApi(req('/api/upload?name=D01Oct26.tou',e.VIEW_TOKEN,'POST',await fixture()),e)).status,401);});
test('valid upload is original bytes; same site/name replaces and sites stay separate',async()=>{const e=env(),bytes=await fixture();let r=await handleApi(req('/api/upload?site=main&name=D01Oct26.tou',e.UPLOAD_TOKEN,'POST',bytes),e);assert.equal(r.status,200);r=await handleApi(req('/api/tou-file?site=main&name=D01Oct26.tou',e.VIEW_TOKEN),e);assert.deepEqual(Buffer.from(await r.arrayBuffer()),bytes);const b=Buffer.from(bytes);b.writeDoubleLE(123,64);assert.equal((await handleApi(req('/api/upload?name=D01Oct26.tou',e.UPLOAD_TOKEN,'POST',b),e)).status,200);assert.equal(e.TOU_BUCKET.objects.size,1);assert.equal((await handleApi(req('/api/tou-file?site=other&name=D01Oct26.tou',e.VIEW_TOKEN),e)).status,404);});
test('list includes every page and only current site',async()=>{const e=env();for(const name of ['D01Oct26.tou','D02Oct26.tou','D01Sep26.tou'])e.TOU_BUCKET.objects.set('main/'+name,new Uint8Array(64));e.TOU_BUCKET.objects.set('other/D02Sep26.tou',new Uint8Array(64));const r=await handleApi(req('/api/tou-files',e.VIEW_TOKEN),e);assert.equal((await r.json()).files.length,3);});
test('rejects invalid paths, invalid binary, missing baseline data and oversized bodies',async()=>{const e=env();for(const query of ['name=../D01Oct26.tou','site=../main&name=D01Oct26.tou','name=D03Oct26.tou'])assert.equal((await handleApi(req('/api/upload?'+query,e.UPLOAD_TOKEN,'POST',await fixture()),e)).status,400);assert.equal((await handleApi(req('/api/upload?name=D01Oct26.tou',e.UPLOAD_TOKEN,'POST',new Uint8Array(128*1024+1)),e)).status,413);assert.equal((await handleApi(req('/api/upload?name=D01Oct26.tou',e.UPLOAD_TOKEN,'POST',new Uint8Array(64)),e)).status,400);const b=Buffer.from(await fixture());assert.equal((await handleApi(req('/api/upload?name=D01Sep26.tou',e.UPLOAD_TOKEN,'POST',b),e)).status,400);});
test('missing or identical tokens fail closed',async()=>{for(const e of [{TOU_BUCKET:new Bucket()},{...env(),UPLOAD_TOKEN:'read-test-token'}])assert.equal((await handleApi(req('/api/tou-files','read-test-token'),e)).status,503);});
