<?php
require __DIR__.'/../neverdie/public-policy.php';
$cases=[
 ['GET','tou-files',['site'=>'main'],true],
 ['GET','tou-file',['site'=>'main'],true],
 ['GET','tou-file',['site'=>'other'],false],
 ['GET','tou-file',[],false],
 ['GET','tou-file',['site'=>['main']],false],
 ['POST','upload',['site'=>'main'],false],
 ['GET','upload',['site'=>'main'],false],
 ['POST','tou-file',['site'=>'main'],false],
 ['GET','unknown',['site'=>'main'],false]
];
foreach($cases as $c)if(ems_public_read($c[0],$c[1],$c[2])!==$c[3])throw new Exception('Public read policy failed');
echo 'Public read policy: '.count($cases)." checks passed\n";
