import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
test('parser and TOU formula match original GitHub blobs apart from line endings',async()=>{
 const source=JSON.parse(await readFile(new URL('../reports/SOURCE.json',import.meta.url),'utf8'));
 for(const name of ['parser.mjs','tou.mjs']){
  const item=source[name],bytes=Buffer.from(item.originalContent);
  const gitSha=createHash('sha1').update(Buffer.from(`blob ${bytes.length}\0`)).update(bytes).digest('hex');
  assert.equal(gitSha,item.gitBlobSha,name+' source provenance');
  const local=await readFile(new URL('../dashboard/'+name,import.meta.url),'utf8');
  assert.equal(local.replaceAll('\r','').trimEnd(),item.originalContent.replaceAll('\r','').trimEnd(),name+' unchanged logic');
 }
});
