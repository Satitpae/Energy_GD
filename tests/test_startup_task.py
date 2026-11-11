import sys,unittest,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'uploader'))
from startup_task import task_xml,NS
class StartupTests(unittest.TestCase):
 def test_boot_action_and_noninteractive_account(self):
  root=ET.fromstring(task_xml(r'C:\Program Files\Sender\TOUSender.exe',r'C:\Users\Field User\config.json',r'FIELD\operator'))
  ns={'t':NS};get=lambda path:root.find(path,ns).text
  self.assertEqual(get('t:Triggers/t:BootTrigger/t:Delay'),'PT1M')
  self.assertEqual(get('t:Principals/t:Principal/t:LogonType'),'Password')
  self.assertEqual(get('t:Actions/t:Exec/t:Arguments'),'--engine --config "C:\\Users\\Field User\\config.json"')
  self.assertEqual(get('t:Settings/t:ExecutionTimeLimit'),'PT0S')
  self.assertEqual(get('t:Settings/t:MultipleInstancesPolicy'),'IgnoreNew')
if __name__=='__main__':unittest.main()
