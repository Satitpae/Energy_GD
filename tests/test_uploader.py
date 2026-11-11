import importlib.util
import json
import tempfile
import unittest
import io
from unittest.mock import patch
from http.client import IncompleteRead
from pathlib import Path

class UploaderTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.root = Path(self.temp.name)
        spec = importlib.util.spec_from_file_location('sender', Path(__file__).parents[1] / 'uploader' / 'send.py')
        self.sender = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.sender)
        self.config = {'folder': str(self.root), 'state_file': str(self.root / 'state.json'), 'base_url': 'https://ems.example', 'site': 'main', 'upload_token': 'test-upload'}
        self.file = self.root / 'D01Oct26.tou'
        self.file.write_bytes(b'first')

    def tearDown(self):
        self.temp.cleanup()

    def test_only_new_or_changed_contents_are_sent(self):
        calls = []
        send = lambda c, n, b: calls.append((n, b))
        self.assertEqual(self.sender.scan_once(self.config, send)['sent'], 1)
        self.assertEqual(self.sender.scan_once(self.config, send)['sent'], 0)
        self.file.write_bytes(b'other')
        self.assertEqual(self.sender.scan_once(self.config, send)['sent'], 1)
        self.assertEqual([body for _, body in calls], [b'first', b'other'])

    def test_failed_send_retries_next_scan_and_does_not_record_success(self):
        def broken(*args):
            raise OSError('offline')
        self.assertEqual(self.sender.scan_once(self.config, broken)['failed'], 1)
        self.assertFalse((self.root / 'state.json').exists())
        self.assertEqual(self.sender.scan_once(self.config, lambda *a: None)['sent'], 1)

    def test_new_destination_resends_and_oversized_file_is_skipped(self):
        self.sender.scan_once(self.config, lambda *a: None)
        self.config['site'] = 'second'
        self.assertEqual(self.sender.scan_once(self.config, lambda *a: None)['sent'], 1)
        self.file.write_bytes(b'x' * (128 * 1024 + 1))
        self.assertEqual(self.sender.scan_once(self.config, lambda *a: None)['failed'], 1)

    def test_dry_run_does_not_send_or_change_state(self):
        def must_not_send(*args):
            self.fail('dry run sent a file')
        self.assertEqual(self.sender.scan_once(self.config, must_not_send, dry_run=True)['pending'], 1)
        self.assertFalse((self.root / 'state.json').exists())

    def test_truncated_http_acknowledgement_retries(self):
        def truncated(*args):
            raise IncompleteRead(b'partial', 100)
        self.assertEqual(self.sender.scan_once(self.config, truncated)['failed'], 1)
        self.assertFalse((self.root / 'state.json').exists())
        self.assertEqual(self.sender.scan_once(self.config, lambda *a: None)['sent'], 1)

    def test_rejected_contents_wait_until_changed_or_explicit_retry(self):
        calls = []
        def reject(c, n, b):
            calls.append(b)
            raise self.sender.UploadRejected('Upload HTTP 400')
        self.assertEqual(self.sender.scan_once(self.config, reject)['failed'], 1)
        self.assertEqual(self.sender.scan_once(self.config, reject)['rejected'], 1)
        self.assertEqual(len(calls), 1)
        self.file.write_bytes(b'changed')
        self.assertEqual(self.sender.scan_once(self.config, reject)['failed'], 1)
        self.config['retry_rejected'] = True
        self.assertEqual(self.sender.scan_once(self.config, lambda *a: None)['sent'], 1)
        self.assertEqual(self.sender.scan_once(self.config, reject)['unchanged'], 1)

    def test_server_or_network_failure_is_not_cached_as_rejected(self):
        calls = []
        def failed(*args):
            calls.append(1)
            raise OSError('Upload HTTP 503')
        self.sender.scan_once(self.config, failed)
        self.sender.scan_once(self.config, failed)
        self.assertEqual(len(calls), 2)

    def test_latest_checked_each_scan_history_resent_once_per_day(self):
        self.config['upload_policy'] = 'latest-month-daily-history'
        old = self.root / 'D01Sep26.tou'
        old.write_bytes(b'old')
        calls = []
        send = lambda c,n,b: calls.append((n,b))
        self.assertEqual(self.sender.scan_once(self.config,send,today='2026-10-26')['sent'],2)
        old.write_bytes(b'old-changed')
        self.file.write_bytes(b'new-latest')
        self.assertEqual(self.sender.scan_once(self.config,send,today='2026-10-26')['sent'],1)
        self.assertEqual(calls[-1],('D01Oct26.tou',b'new-latest'))
        self.assertEqual(self.sender.scan_once(self.config,send,today='2026-10-27')['sent'],1)
        self.assertEqual(calls[-1],('D01Sep26.tou',b'old-changed'))
        self.assertEqual(self.sender.scan_once(self.config,send,today='2026-10-27')['sent'],0)

    def test_history_rejection_is_retried_next_day_not_every_minute(self):
        self.config['upload_policy'] = 'latest-month-daily-history'
        old = self.root / 'D01Sep26.tou';old.write_bytes(b'old')
        calls = []
        def send(c,n,b):
            calls.append(n)
            if n==old.name:raise self.sender.UploadRejected('HTTP 400')
        self.sender.scan_once(self.config,send,today='2026-10-26')
        self.sender.scan_once(self.config,send,today='2026-10-26')
        self.assertEqual(calls.count(old.name),1)
        self.sender.scan_once(self.config,send,today='2026-10-27')
        self.assertEqual(calls.count(old.name),2)

    def test_month_rollover_uses_numeric_month_and_latest_per_meter(self):
        self.config['upload_policy'] = 'latest-month-daily-history'
        (self.root/'D01Nov26.tou').write_bytes(b'nov')
        (self.root/'D02Sep26.tou').write_bytes(b'solar')
        calls=[];send=lambda c,n,b:calls.append(n)
        self.sender.scan_once(self.config,send,today='2026-11-01')
        (self.root/'D02Sep26.tou').write_bytes(b'solar-update')
        self.file.write_bytes(b'oct-update')
        self.sender.scan_once(self.config,send,today='2026-11-01')
        self.assertEqual(calls.count('D01Oct26.tou'),1)
        self.assertEqual(calls.count('D02Sep26.tou'),2)

    def test_invalid_acknowledgement_shape_is_a_retryable_error(self):
        for raw in ['null','[]','true','"ok"']:
            with self.subTest(raw=raw), patch.object(self.sender.urllib.request,'build_opener') as opener:
                opener.return_value.open.return_value.__enter__.return_value=io.StringIO(raw)
                with self.assertRaises(OSError):
                    self.sender.send_http(self.config,self.file.name,b'first')

    def test_stop_interrupts_between_files_and_before_first_file(self):
        (self.root/'D02Oct26.tou').write_bytes(b'second')
        calls=[]
        result=self.sender.scan_once(self.config,lambda *args:calls.append(1),stop_requested=lambda:len(calls)>=1)
        self.assertEqual(len(calls),1)
        self.assertTrue(result['stopped'])
        result=self.sender.scan_once(self.config,lambda *args:self.fail('must stop'),stop_requested=lambda:True)
        self.assertTrue(result['stopped'])
    def test_heartbeat_uses_upload_token_and_sends_no_file_contents(self):
        self.config['api_style']='php'
        with patch.object(self.sender.urllib.request,'build_opener') as opener:
            opener.return_value.open.return_value.__enter__.return_value=io.StringIO('{"ok":true,"last_seen_at":"2026-10-26T12:00:00Z"}')
            ack=self.sender.send_heartbeat(self.config,True)
            req=opener.return_value.open.call_args.args[0]
            self.assertIn('action=sender-heartbeat',req.full_url)
            self.assertEqual(req.get_header('Authorization'),'Bearer test-upload')
            self.assertEqual(json.loads(req.data),{'scan_ok':True})
            self.assertTrue(ack['ok'])

if __name__ == '__main__':
    unittest.main()
