import {mkdir,readFile,writeFile,copyFile,readdir} from 'node:fs/promises';
const root=new URL('../',import.meta.url),out=new URL('dist/',root);
await mkdir(new URL('dashboard/',out),{recursive:true});
// Explicit allowlist: no field data, reports, uploader settings or credential files.
const names=['index.html','style.css','app.js','parser.mjs','tou.mjs','excel.mjs','view.mjs','trial.mjs','selection.mjs'];
for(const name of names)await copyFile(new URL('dashboard/'+name,root),new URL('dashboard/'+name,out));
await writeFile(new URL('dashboard/mode.js',out),'window.EMS_ONLINE = true;\n');
await writeFile(new URL('_redirects',out),'/ /dashboard/ 302\n');
await writeFile(new URL('_routes.json',out),JSON.stringify({version:1,include:['/api/*'],exclude:[]}));
await writeFile(new URL('_headers',out),"/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer\n  X-Frame-Options: DENY\n  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'; form-action 'self'\n");
const allowed=new Set(['dashboard', '_redirects','_routes.json','_headers']);
for(const f of await readdir(out))if(!allowed.has(f))throw Error('Unexpected deployment file: '+f);
for(const f of await readdir(new URL('dashboard/',out)))if(![...names,'mode.js'].includes(f))throw Error('Unexpected dashboard file: '+f);
console.log('Cloud build ready: dist (static dashboard only; no TOU data or secrets).');
