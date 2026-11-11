<?php
// Compatible with PHP 7.4+. Data and tokens must live outside the web root.
function ems_json($data,$status=200){return ['status'=>$status,'headers'=>['Content-Type'=>'application/json; charset=utf-8'],'body'=>json_encode($data,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES)];}
function ems_error($message,$status){throw new RuntimeException($message,$status);}
function ems_name($raw){
 if(!is_string($raw)||!preg_match('/^(D0[12])(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{2})\.tou$/iD',$raw,$m))ems_error('Invalid TOU filename',400);
 return strtoupper($m[1]).ucfirst(strtolower($m[2])).$m[3].'.tou';
}
function ems_validate($bytes,$name){
 $size=strlen($bytes);
 if($size<96||substr($bytes,0,8)!=="TOUReg\0\0"||unpack('v',substr($bytes,8,2))[1]!==64||($size-64)%16!==0)ems_error('Invalid TOUReg binary',400);
 preg_match('/^D0[12]([A-Za-z]{3})(\d{2})\.tou$/D',$name,$p);
 $months=['Jan'=>1,'Feb'=>2,'Mar'=>3,'Apr'=>4,'May'=>5,'Jun'=>6,'Jul'=>7,'Aug'=>8,'Sep'=>9,'Oct'=>10,'Nov'=>11,'Dec'=>12];
 $month=$months[$p[1]];$year=2000+(int)$p[2];
 if(substr($bytes,10,18)!==sprintf('01/%02d/%04d00:00:00',$month,$year))ems_error('Header month does not match filename',400);
 $active=false;$monthRows=(int)date('t',gmmktime(0,0,0,$month,1,$year))*96;
 for($i=0;$i<($size-64)/16;$i++){
  $d=unpack('e',substr($bytes,64+$i*16,8))[1];$e=unpack('e',substr($bytes,72+$i*16,8))[1];
  if(!is_finite($d)||!is_finite($e))ems_error('Non-finite reading',400);
  if($i<$monthRows&&($d!=0||$e!=0))$active=true;
 }
 if(!$active)ems_error('No readings in selected month',400);
}
function ems_handle($method,$action,$query,$token,$body,$config){
 $lock=null;
 try{
  if(empty($config['view_token'])||empty($config['upload_token'])||$config['view_token']===$config['upload_token']||empty($config['data_dir']))ems_error('Service not configured',503);
  $expected=$action==='upload'?$config['upload_token']:$config['view_token'];
  if(!is_string($token)||!hash_equals($expected,$token))ems_error('Unauthorized',401);
  $site=isset($query['site'])?$query['site']:'main';
  if(!is_string($site)||!preg_match('/^[a-z0-9][a-z0-9_-]{0,47}$/D',$site))ems_error('Invalid site',400);
  if(!in_array($action,['tou-files','tou-file','upload'],true))ems_error('Not found',404);
  if($method!==($action==='upload'?'POST':'GET'))ems_error('Method not allowed',405);
  $limit=isset($config['max_file_bytes'])?$config['max_file_bytes']:131072;
  if(strlen($body)>$limit)ems_error('File exceeds 128 KiB',413);
  $name=$action==='tou-files'?null:ems_name(isset($query['name'])?$query['name']:'');
  if($action==='upload')ems_validate($body,$name);
  $data=rtrim($config['data_dir'],'/\\');
  if(!is_dir($data)&&!mkdir($data,0700,true))ems_error('Storage unavailable',503);
  $lock=fopen($data.'/.lock','c+');if(!$lock||!flock($lock,LOCK_EX))ems_error('Storage busy',503);
  $dir=$data.'/'.$site;$path=$name?$dir.'/'.$name:null;
  if($path&&is_link($path))ems_error('Invalid storage path',400);
  if(is_link($dir))ems_error('Invalid site storage',400);
  if($action==='tou-files'){
   $files=[];foreach(glob($dir.'/*.tou')?:[] as $file){if(is_file($file)&&!is_link($file))$files[]=['name'=>basename($file),'size'=>filesize($file)];}
   $response=ems_json(['site'=>$site,'files'=>$files]);
  }elseif($action==='tou-file'){
   if(!is_file($path))ems_error('File not found',404);
   if(filesize($path)>$limit)ems_error('Stored file exceeds limit',413);
   $contents=file_get_contents($path);if($contents===false)ems_error('Read failed',503);
   $response=['status'=>200,'headers'=>['Content-Type'=>'application/octet-stream','Content-Disposition'=>'attachment; filename="'.$name.'"'],'body'=>$contents];
  }else{
   $used=0;foreach(glob($data.'/*/*.tou')?:[] as $file){if(is_file($file)&&!is_link($file))$used+=filesize($file);}
   $old=is_file($path)?filesize($path):0;
   if($used-$old+strlen($body)>$config['max_storage_bytes'])ems_error('Application storage ceiling reached',507);
   $response=ems_json(['ok'=>true,'site'=>$site,'name'=>$name,'size'=>strlen($body)]);
  }
  $usagePath=$data.'/.usage.json';$usage=is_file($usagePath)?json_decode(file_get_contents($usagePath),true):[];
  if(!is_array($usage))ems_error('Usage counter unavailable',503);
  $month=gmdate('Y-m');$day=gmdate('Y-m-d');
  if(!isset($usage['month'])||$usage['month']!==$month)$usage=['month'=>$month,'bytes'=>0,'day'=>$day,'requests'=>0];
  if($usage['day']!==$day){$usage['day']=$day;$usage['requests']=0;}
  $transfer=strlen($body)+strlen($response['body']);
  if($usage['bytes']+$transfer>$config['max_month_bytes']||$usage['requests']+1>$config['max_day_requests'])ems_error('Application usage ceiling reached; try later',429);
  // Reserve usage before sending bytes or changing files. A failed write consumes its reservation.
  $usage['bytes']+=$transfer;$usage['requests']++;
  $usageTemp=$usagePath.'.tmp';if(file_put_contents($usageTemp,json_encode($usage))===false||!rename($usageTemp,$usagePath))ems_error('Usage counter write failed',503);
  if($action==='upload'){
   if(!is_dir($dir)&&!mkdir($dir,0700,true))ems_error('Storage creation failed',503);
   $temp=tempnam($dir,'.upload-');if($temp===false)ems_error('Storage creation failed',503);
   if(file_put_contents($temp,$body)!==strlen($body)||!rename($temp,$path)){if(is_file($temp))unlink($temp);ems_error('Upload write failed',503);}
   chmod($path,0600);
  }
  return $response;
 }catch(Throwable $e){$code=(int)$e->getCode();return ems_json(['error'=>$code>=400&&$code<=599?$e->getMessage():'Storage operation failed'],$code>=400&&$code<=599?$code:500);}
 finally{if(is_resource($lock)){flock($lock,LOCK_UN);fclose($lock);}}
}
