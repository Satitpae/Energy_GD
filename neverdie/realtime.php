<?php
ini_set('display_errors','0');
header('Content-Type: application/json; charset=utf-8');header('Cache-Control: no-store');header('X-Content-Type-Options: nosniff');
function rt_reply($data,$code=200){http_response_code($code);$bytes=json_encode($data,JSON_UNESCAPED_UNICODE);if(strpos($_SERVER['HTTP_ACCEPT_ENCODING']??'','gzip')!==false){header('Content-Encoding: gzip');header('Vary: Accept-Encoding');$bytes=gzencode($bytes,6);}echo $bytes;exit;}
$private=dirname(__DIR__,4).'/.php/granddigital-ems-tou-private';
if(!is_readable($private.'/config.php'))rt_reply(['error'=>'Service unavailable'],503);
$config=require $private.'/config.php';
$method=$_SERVER['REQUEST_METHOD'];$write=$method==='POST';
if(!in_array($method,['GET','POST'],true))rt_reply(['error'=>'Method not allowed'],405);
if($write){$auth=$_SERVER['HTTP_AUTHORIZATION']??($_SERVER['REDIRECT_HTTP_AUTHORIZATION']??'');if(!hash_equals('Bearer '.$config['upload_token'],$auth))rt_reply(['error'=>'Unauthorized'],401);}
$day=$_GET['date']??'';$interval=$_GET['interval']??'1';$site=$_GET['site']??'main';
if($site!=='main'||!is_string($day)||!preg_match('/^20[0-9]{2}-[0-9]{2}-[0-9]{2}$/D',$day)||!in_array($interval,['1','5','15','30','60'],true)||date('Y-m-d',strtotime($day))!==$day)rt_reply(['error'=>'Invalid selection'],400);
$dir=rtrim($config['data_dir'],'/\\').'/realtime';
if(!is_dir($dir)&&!mkdir($dir,0700,true))rt_reply(['error'=>'Storage unavailable'],503);
$path=$dir.'/'.$day.'-'.$interval.'.json.gz';
$lock=fopen($dir.'/.lock','c+');if(!$lock||!flock($lock,$write?LOCK_EX:LOCK_SH))rt_reply(['error'=>'Storage busy'],503);
if(is_link($path))rt_reply(['error'=>'Storage unavailable'],503);
if($write){
 if((int)($_SERVER['CONTENT_LENGTH']??0)>1048576)rt_reply(['error'=>'Payload too large'],413);
 $body=file_get_contents('php://input',false,null,0,1048577);if(strlen($body)>1048576)rt_reply(['error'=>'Payload too large'],413);
 $raw=@gzdecode($body,4194304);$data=$raw===false?null:json_decode($raw,true);
 if(!is_array($data)||($data['selected_date']??'')!==$day||($data['interval_minutes']??0)!==(int)$interval||count($data['devices']??[])!==2)rt_reply(['error'=>'Invalid snapshot'],400);
 $fields=['kW','kWh','Demand','AccDem','kVA','kVar','PF','Hz','VoltageL1','VoltageL2','VoltageL3','CurrentL1','CurrentL2','CurrentL3','THDVoltageL1','THDVoltageL2','THDVoltageL3','THDCurrentL1','THDCurrentL2','THDCurrentL3'];
 $clean=['ok'=>true,'selected_date'=>$day,'interval_minutes'=>(int)$interval,'window_end'=>$day.'T00:00:00+07:00','devices'=>[]];
 $clean['window_end']=date('Y-m-d',strtotime($day.' +1 day')).'T00:00:00+07:00';
 $cleanRow=function($row)use($day,$fields){if($row===null)return null;if(!is_array($row)||!is_string($row['DataDateTime']??null)||!preg_match('/^'.preg_quote($day,'/').' [0-2][0-9]:[0-5][0-9]:[0-5][0-9]$/D',$row['DataDateTime']))rt_reply(['error'=>'Invalid reading'],400);$out=['DataDateTime'=>$row['DataDateTime']];foreach($fields as $f){$v=$row[$f]??null;if($v!==null&&(!is_int($v)&&!is_float($v)||!is_finite((float)$v)))rt_reply(['error'=>'Invalid value'],400);$out[$f]=$v;}return $out;};
 foreach(['MEA','Solar Cell'] as $i=>$name){$d=$data['devices'][$i];if(($d['name']??'')!==$name||!is_array($d['history']??null)||count($d['history'])>1440)rt_reply(['error'=>'Invalid device'],400);$clean['devices'][]=['name'=>$name,'latest'=>$cleanRow($d['latest']??null),'last_row_at'=>$d['last_row_at']??null,'daily_peak'=>$cleanRow($d['daily_peak']??null),'history'=>array_map($cleanRow,$d['history'])];}
 $clean['received_at']=gmdate('c');$bytes=gzencode(json_encode($clean),6);$used=0;foreach(glob($dir.'/*.gz')?:[] as $f)$used+=filesize($f);
 if($used+strlen($bytes)-(is_file($path)?filesize($path):0)>104857600)rt_reply(['error'=>'Storage ceiling reached'],507);
 $tmp=tempnam($dir,'.rt-');if(!$tmp||file_put_contents($tmp,$bytes)!==strlen($bytes)||!rename($tmp,$path))rt_reply(['error'=>'Storage write failed'],503);chmod($path,0600);
 rt_reply(['ok'=>true,'date'=>$day,'interval'=>(int)$interval]);
}
if(!is_file($path))rt_reply(['error'=>'No data for selected date'],404);
$data=json_decode(gzdecode(file_get_contents($path)),true);if(!is_array($data))rt_reply(['error'=>'Data unavailable'],503);
$data['server_time']=gmdate('c');foreach($data['devices'] as &$d){$stamp=$d['latest']['DataDateTime']??null;$age=$stamp?time()-strtotime($stamp.' +0700'):null;$d['age_seconds']=$age;$d['stale']=$age===null||$age>180;}unset($d);
rt_reply($data);
