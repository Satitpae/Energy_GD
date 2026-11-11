import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

class DesktopTest(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('desktop_core',Path(__file__).parents[1]/'uploader/desktop_core.py')
        self.core=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.core)
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.root=Path(self.temp.name)
        self.seed={'base_url':'https://energy.granddigital.co.th','site':'main','upload_token':'test-private-token','folder':'C:/HView/System'}
    def tearDown(self):self.temp.cleanup()
    def test_initialization_preserves_user_configuration_and_uses_private_runtime(self):
        path=self.core.ensure_config(self.root,self.seed)
        c=json.loads(path.read_text());self.assertEqual(c['upload_policy'],'latest-month-daily-history')
        self.assertEqual(c['interval_seconds'],60);self.assertEqual(c['state_file'],'state.json')
        c['folder']='D:/Energy';path.write_text(json.dumps(c))
        self.assertEqual(json.loads(self.core.ensure_config(self.root,self.seed).read_text())['folder'],'D:/Energy')
    def test_invalid_destination_is_rejected_before_saving(self):
        self.seed['base_url']='http://example.com'
        with self.assertRaises(ValueError):self.core.ensure_config(self.root,self.seed)
        self.assertFalse((self.root/'config.json').exists())
    def test_frozen_worker_and_status_do_not_launch_gui_or_depend_on_python(self):
        path=self.root/'config.json'
        command=self.core.command_for('status',path,True,'C:/Apps/TOUSender.exe')
        self.assertEqual(command,['C:/Apps/TOUSender.exe','--engine','--config',str(path),'--status'])
        self.assertEqual(self.core.command_for('start',path,True,'C:/Apps/TOUSender.exe')[-3:],['--engine','--config',str(path)])
    def test_credential_free_install_stays_unconfigured_until_import(self):
        self.seed.pop('upload_token')
        p=self.core.ensure_config(self.root,self.seed)
        config=json.loads(p.read_text())
        self.assertNotIn('upload_token',config)
        with self.assertRaises(ValueError):self.core.save_config(p,config)
    def test_gui_lock_can_be_observed_and_released(self):
        lock=self.core.acquire_lock(self.root,'ui.lock')
        self.assertIsNotNone(lock)
        self.assertTrue(self.core.is_running(self.root,'ui.lock'))
        self.assertIsNone(self.core.acquire_lock(self.root,'ui.lock'))
        lock.close()
        self.assertFalse(self.core.is_running(self.root,'ui.lock'))
    def test_older_partial_configuration_gets_php_route_without_losing_folder(self):
        p=self.root/'config.json';c={**self.seed,'folder':'D:/Energy'}
        p.write_text(json.dumps(c))
        self.core.ensure_config(self.root,self.seed)
        loaded=json.loads(p.read_text())
        self.assertEqual(loaded['api_style'],'php')
        self.assertEqual(loaded['folder'],'D:/Energy')
        self.assertEqual(loaded['upload_token'],'test-private-token')
