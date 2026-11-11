import {randomBytes} from 'node:crypto';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
const root=new URL('../',import.meta.url),privateDir=new URL('.local/',root);
await mkdir(privateDir,{recursive:true});
const path=new URL('pages-secrets.json',privateDir);let secrets;
try{secrets=JSON.parse(await readFile(path,'utf8'));}catch(e){if(e.code!=='ENOENT')throw e;secrets={VIEW_TOKEN:randomBytes(32).toString('base64url'),UPLOAD_TOKEN:randomBytes(32).toString('base64url')};await writeFile(path,JSON.stringify(secrets,null,2),{mode:0o600});}
if(!secrets.VIEW_TOKEN||!secrets.UPLOAD_TOKEN||secrets.VIEW_TOKEN===secrets.UPLOAD_TOKEN)throw Error('Invalid secrets');
await writeFile(new URL('view-token.txt',privateDir),'Site: main\nView token:\n'+secrets.VIEW_TOKEN+'\n',{mode:0o600});
const uploaderPath=new URL('uploader/config.local.json',root);
try{await readFile(uploaderPath);}catch(e){if(e.code!=='ENOENT')throw e;await writeFile(uploaderPath,JSON.stringify({base_url:'https://granddigital-ems-tou.pages.dev',site:'main',folder:'../TOU File for test',upload_token:secrets.UPLOAD_TOKEN,state_file:'state-main.json',interval_seconds:60},null,2),{mode:0o600});}
console.log('Private tokens and uploader configuration prepared. Token values are not printed.');
