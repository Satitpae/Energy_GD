<?php
function ems_public_read($method,$action,$query){
 return $method==='GET'&&in_array($action,['tou-files','tou-file','sender-status'],true)&&isset($query['site'])&&$query['site']==='main';
}
