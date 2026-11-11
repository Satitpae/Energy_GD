<?php
// Small, separate heartbeat store: never derive connectivity from reads or TOU timestamps.
function ems_sender_handle($method,$action,$query,$token,$body,$config,$now=null){
 $lock=null;$now=$now===null?time():$now;
 try{
  $write=$action==='sender-heartbeat';$expected=$write?$config['upload_token']:$config['view_token'];
  if(!$token||!is_string($token)||!hash_equals($expected,$token))ems_error('Unauthorized',401);
  if($method!==($write?'POST':'GET'))ems_error('Method not allowed',405);
  $site=isset($query['site'])?$query['site']:'main';
  if(!is_string($site)||!preg_match('/^[a-z0-9][a-z0-9_-]{0,47}$/D',$site))ems_error('Invalid site',400);
  if(strlen($body)>1024)ems_error('Heartbeat exceeds limit',413);
  $payload=$write?json_decode($body,true):[];
  if($write&&(!is_array($payload)||!array_key_exists('scan_ok',$payload)||(!is_bool($payload['scan_ok'])&&$payload['scan_ok']!==null)))ems_error('Invalid heartbeat',400);
  $dir=rtrim($config['data_dir'],'/\\');
  if(is_link($dir))ems_error('Invalid storage',400);
  if(!is_dir($dir)&&!mkdir($dir,0700,true))ems_error('Storage unavailable',503);
  $lock=fopen($dir.'/.sender.lock','c+');if(!$lock||!flock($lock,$write?LOCK_EX:LOCK_SH))ems_error('Storage busy',503);
  $path=$dir.'/.sender-'.$site.'.json';if(is_link($path))ems_error('Invalid storage',400);
  $last=is_file($path)?json_decode(file_get_contents($path),true):null;
  if(is_file($path)&&!is_array($last))ems_error('Sender state unavailable',503);
  if($write){
   if($last&&$now-$last['seen_unix']<10)ems_error('Heartbeat rate limited',429);
   $last=['seen_unix'=>$now,'last_seen_at'=>gmdate('Y-m-d\TH:i:s\Z',$now),'scan_ok'=>$payload['scan_ok']];
   $temp=tempnam($dir,'.sender-');$bytes=json_encode($last);
   if($temp===false||file_put_contents($temp,$bytes)!==strlen($bytes)||!rename($temp,$path)){if($temp&&is_file($temp))unlink($temp);ems_error('Heartbeat write failed',503);}
   chmod($path,0600);
  }
  return ems_json(['ok'=>true,'last_seen_at'=>$last?$last['last_seen_at']:null,'scan_ok'=>$last?$last['scan_ok']:null,'server_time'=>gmdate('Y-m-d\TH:i:s\Z',$now),'stale_after_seconds'=>180]);
 }catch(Throwable $e){$code=(int)$e->getCode();return ems_json(['error'=>$code>=400&&$code<=599?$e->getMessage():'Sender state unavailable'],$code>=400&&$code<=599?$code:500);}
 finally{if(is_resource($lock)){flock($lock,LOCK_UN);fclose($lock);}}
}
