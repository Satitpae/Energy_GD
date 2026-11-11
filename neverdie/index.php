<?php
ini_set('display_errors','0');
header('Cache-Control: no-store');header('X-Content-Type-Options: nosniff');header('Referrer-Policy: no-referrer');
$private=dirname(__DIR__,4).'/.php/granddigital-ems-tou-private';
if(!is_readable($private.'/config.php')||!is_readable($private.'/api-lib.php')){http_response_code(503);header('Content-Type: application/json');echo '{"error":"Service not configured"}';exit;}
require $private.'/api-lib.php';$config=require $private.'/config.php';
// Daily historical resends plus public dashboard reads; monthly byte ceiling remains unchanged.
$config['max_day_requests']=2000;
require __DIR__.'/public-policy.php';
require __DIR__.'/sender-status.php';
$auth=isset($_SERVER['HTTP_AUTHORIZATION'])?$_SERVER['HTTP_AUTHORIZATION']:(isset($_SERVER['REDIRECT_HTTP_AUTHORIZATION'])?$_SERVER['REDIRECT_HTTP_AUTHORIZATION']:'');
$token=preg_match('/^Bearer (.+)$/D',$auth,$m)?$m[1]:'';
$action=isset($_GET['action'])?$_GET['action']:'';
if(!is_string($action))$action='';
// Only the approved main site's read routes are public. Upload authorization is unchanged.
if(ems_public_read($_SERVER['REQUEST_METHOD'],$action,$_GET))$token=$config['view_token'];
$expected=in_array($action,['upload','sender-heartbeat'],true)?$config['upload_token']:$config['view_token'];
if(!$token||!hash_equals($expected,$token)){$response=ems_json(['error'=>'Unauthorized'],401);}
elseif(isset($_SERVER['CONTENT_LENGTH'])&&(int)$_SERVER['CONTENT_LENGTH']>131072){$response=ems_json(['error'=>'File exceeds 128 KiB'],413);}
else{$stream=fopen('php://input','rb');$body=stream_get_contents($stream,131073);fclose($stream);$response=in_array($action,['sender-status','sender-heartbeat'],true)?ems_sender_handle($_SERVER['REQUEST_METHOD'],$action,$_GET,$token,$body,$config):ems_handle($_SERVER['REQUEST_METHOD'],$action,$_GET,$token,$body,$config);}
http_response_code($response['status']);foreach($response['headers'] as $key=>$value)header($key.': '.$value);echo $response['body'];
