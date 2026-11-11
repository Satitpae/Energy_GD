<?php
require __DIR__.'/../neverdie/api-lib.php';
require __DIR__.'/../neverdie/sender-status.php';
$root=__DIR__.'/heartbeat-'.bin2hex(random_bytes(4));mkdir($root);
$config=['data_dir'=>$root,'view_token'=>'view','upload_token'=>'upload'];$checks=0;
function expect_status($yes){global $checks;if(!$yes)throw new Exception('Heartbeat check failed');$checks++;}
try{
 $q=['site'=>'main'];$now=1700000000;
 $r=ems_sender_handle('GET','sender-status',$q,'view','',$config,$now);$j=json_decode($r['body'],true);
 expect_status($r['status']===200&&$j['last_seen_at']===null);
 expect_status(ems_sender_handle('POST','sender-heartbeat',$q,'view','{}',$config,$now)['status']===401);
 expect_status(ems_sender_handle('POST','sender-heartbeat',$q,'upload','{"scan_ok":true}',$config,$now)['status']===200);
 $a=json_decode(ems_sender_handle('GET','sender-status',$q,'view','',$config,$now+60)['body'],true);
 $b=json_decode(ems_sender_handle('GET','sender-status',$q,'view','',$config,$now+180)['body'],true);
 expect_status($a['last_seen_at']===$b['last_seen_at']);
 expect_status($b['server_time']!==$a['server_time']);
 expect_status($a['scan_ok']===true&&$a['stale_after_seconds']===180);
 expect_status(ems_sender_handle('POST','sender-heartbeat',$q,'upload','{"scan_ok":null}',$config,$now+5)['status']===429);
 expect_status(ems_sender_handle('POST','sender-heartbeat',['site'=>'../bad'],'upload','{}',$config,$now+60)['status']===400);
 expect_status(ems_sender_handle('POST','sender-heartbeat',$q,'upload',str_repeat('x',1025),$config,$now+60)['status']===413);
 expect_status(ems_sender_handle('GET','sender-heartbeat',$q,'upload','',$config,$now+60)['status']===405);
 echo "Sender status checks passed: $checks\n";
}finally{foreach(glob($root.'/*')?:[] as $p)unlink($p);foreach(glob($root.'/.*')?:[] as $p)if(is_file($p))unlink($p);rmdir($root);}
