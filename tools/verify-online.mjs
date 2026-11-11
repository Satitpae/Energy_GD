import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const base='http://127.0.0.1:8767';
assert.equal((await fetch(base+'/api/tou-files')).status,401);
for(const name of ['D01Sep26.tou','D02Sep26.tou','D01Oct26.tou','D02Oct26.tou']){
 const bytes=await readFile(new URL('../TOU File for test/'+name,import.meta.url));
 const response=await fetch(base+'/api/upload?site=main&name='+name,{method:'POST',headers:{Authorization:'Bearer integration-upload'},body:bytes});
 assert.equal(response.status,200,await response.text());
 const stored=await fetch(base+'/api/tou-file?site=main&name='+name,{headers:{Authorization:'Bearer integration-view'}});
 assert.deepEqual(Buffer.from(await stored.arrayBuffer()),bytes);
}
const list=await fetch(base+'/api/tou-files?site=main',{headers:{Authorization:'Bearer integration-view'}});
assert.equal((await list.json()).files.length,4);
assert.equal((await fetch(base+'/TOU%20File%20for%20test/D01Oct26.tou')).status,404);
console.log('Online integration passed: anonymous denied, four original files uploaded and read back, private data absent from static assets.');
