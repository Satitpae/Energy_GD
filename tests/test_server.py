import importlib.util
import tempfile
import unittest
from pathlib import Path

class ManifestTest(unittest.TestCase):
    def test_discovers_supported_months_without_hardcoded_names(self):
        spec = importlib.util.spec_from_file_location('local_server', Path(__file__).parents[1] / 'local_server.py')
        server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(server)
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as folder:
            root = Path(folder)
            for name in ['D01Sep26.tou', 'D02Oct26.tou', 'D01Jan27.TOU', 'notes.txt', 'D03Oct26.tou']:
                (root / name).write_bytes(b'123')
            (root / 'D02Sep26.tou').mkdir()
            files = server.list_tou_files(root)
            self.assertEqual([f['name'] for f in files], ['D01Jan27.TOU', 'D01Sep26.tou', 'D02Oct26.tou'])
            self.assertTrue(all(f['size'] == 3 for f in files))
            (root / 'D02Feb27.tou').write_bytes(b'new')
            self.assertEqual(len(server.list_tou_files(root)), 4)

    def test_missing_folder_returns_empty_list(self):
        spec = importlib.util.spec_from_file_location('local_server', Path(__file__).parents[1] / 'local_server.py')
        server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(server)
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as folder:
            self.assertEqual(server.list_tou_files(Path(folder) / 'missing'), [])

if __name__ == '__main__':
    unittest.main()
