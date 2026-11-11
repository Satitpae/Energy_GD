"""Generate a Windows Scheduler definition without registering a task or storing passwords."""
import xml.etree.ElementTree as ET
from pathlib import Path
NS='http://schemas.microsoft.com/windows/2004/02/mit/task'
ET.register_namespace('',NS)
def task_xml(executable,config_path,user):
 root=ET.Element('{'+NS+'}Task',{'version':'1.2'})
 def add(parent,name,text=None,**attrs):
  el=ET.SubElement(parent,'{'+NS+'}'+name,attrs)
  if text is not None:el.text=str(text)
  return el
 info=add(root,'RegistrationInfo');add(info,'Description','Grand Digital TOU Sender: start sending automatically after Windows boots.')
 trigger=add(add(root,'Triggers'),'BootTrigger');add(trigger,'Enabled','true');add(trigger,'Delay','PT1M')
 principal=add(add(root,'Principals'),'Principal',id='SenderUser');add(principal,'UserId',user);add(principal,'LogonType','Password');add(principal,'RunLevel','LeastPrivilege')
 settings=add(root,'Settings')
 for key,value in [('MultipleInstancesPolicy','IgnoreNew'),('DisallowStartIfOnBatteries','false'),('StopIfGoingOnBatteries','false'),('StartWhenAvailable','true'),('RunOnlyIfNetworkAvailable','false'),('AllowStartOnDemand','true'),('Enabled','true'),('ExecutionTimeLimit','PT0S')]:add(settings,key,value)
 restart=add(settings,'RestartOnFailure');add(restart,'Interval','PT1M');add(restart,'Count','3')
 action=add(add(root,'Actions',Context='SenderUser'),'Exec');add(action,'Command',executable);add(action,'Arguments','--engine --config "'+str(config_path)+'"');add(action,'WorkingDirectory',str(Path(executable).parent))
 return ET.tostring(root,encoding='utf-16',xml_declaration=True)
def export_task(executable,config_path,user,output):
 output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(task_xml(str(executable),str(config_path),user));return output
