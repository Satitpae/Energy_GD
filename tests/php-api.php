<?php
require __DIR__.'/../neverdie/api-lib.php';
$root=__DIR__.'/php-trial-'.bin2hex(random_bytes(6));mkdir($root);
$config=['view_token'=>'test-view','upload_token'=>'test-upload','data_dir'=>$root.'/data','max_file_bytes'=>131072,'max_storage_bytes'=>104857600,'max_month_bytes'=>419430400,'max_day_requests'=>1000];
$bytes=file_get_contents(__DIR__.'/../TOU File for test/D01Oct26.tou');$count=0;
function check($value,$message){global $count;if(!$value)throw new Exception($message);$count++;}
function call_api($action,$token,$method='GET',$body='',$query=[]){global $config;return ems_handle($method,$action,$query+['site'=>'main','name'=>'D01Oct26.tou'],$token,$body,$config);}
try{
 check(call_api('tou-files','')['status']===401,'anonymous denied');
 check(call_api('upload','test-view','POST',$bytes)['status']===401,'view cannot upload');
 check(call_api('tou-files','test-upload')['status']===401,'upload cannot view');
 check(call_api('upload','test-upload','POST',$bytes)['status']===200,'valid upload');
 check(call_api('tou-file','test-view')['body']===$bytes,'original bytes');
 check(call_api('tou-file','test-view','GET','',['site'=>'other'])['status']===404,'site isolation');
 check(call_api('upload','test-upload','POST',$bytes,['name'=>'../D01Oct26.tou'])['status']===400,'path rejected');
 check(call_api('upload','test-upload','POST',$bytes,['name'=>'D01Sep26.tou'])['status']===400,'month mismatch');
 check(call_api('upload','test-upload','POST',str_repeat('x',131073))['status']===413,'oversize');
 check(call_api('upload','test-upload','POST',str_repeat('x',64))['status']===400,'bad binary');
 $other=$bytes; $other=substr_replace($other,pack('e',123.0),64,8);
 check(call_api('upload','test-upload','POST',$other)['status']===200,'replace file');
 check(call_api('tou-file','test-view')['body']===$other,'replacement bytes');
 $list=json_decode(call_api('tou-files','test-view')['body'],true);check(count($list['files'])===1,'one canonical file');
 $config['max_storage_bytes']=1;check(call_api('upload','test-upload','POST',$bytes)['status']===507,'storage ceiling');$config['max_storage_bytes']=104857600;
 $config['max_month_bytes']=1;check(call_api('tou-file','test-view')['status']===429,'transfer ceiling');$config['max_month_bytes']=419430400;
 $config['max_day_requests']=1;check(call_api('tou-files','test-view')['status']===429,'daily ceiling');
 echo "PHP API checks passed: $count\n";
}finally{
 function cleanup_trial($path,$base){$real=realpath($path);if($real===false)return;if(strpos($real,$base)!==0)throw new Exception('Unsafe cleanup');foreach(scandir($real) as $name){if($name==='.'||$name==='..')continue;$p=$real.DIRECTORY_SEPARATOR.$name;if(is_dir($p))cleanup_trial($p,$base);else unlink($p);}rmdir($real);}
 cleanup_trial($root,realpath($root));
}
