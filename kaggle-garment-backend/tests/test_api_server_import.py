import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


class ApiServerImportTest(unittest.TestCase):
    def test_imports_with_portable_working_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['GARMENT_WORKING_DIR'] = tmpdir
            spec = importlib.util.spec_from_file_location('api_server', 'kaggle-garment-backend/api_server.py')
            self.assertIsNotNone(spec)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertEqual(module.WORKING_DIR, Path(tmpdir).resolve())
            self.assertTrue((Path(tmpdir).resolve() / 'weights').exists())


if __name__ == '__main__':
    unittest.main()
