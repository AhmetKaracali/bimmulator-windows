import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
checked_config = runpy.run_path(str(TOOLS / "idrive6-launch.py"))["checked_config"]


class LaunchConfigTests(unittest.TestCase):
    def config(self, **options):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            file = project / "idrive6.toml"
            file.touch()
            output = json.dumps({"psdzdata": str(root / "psdzdata"), **options})
            with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0, stdout=output)):
                return checked_config(project, file, "nix")

    def test_module_selection_defaults_to_both_ecus(self):
        self.assertEqual(self.config()["modules"], ["head-unit", "6wb"])

    def test_module_selection_can_start_either_ecu(self):
        for module in ("head-unit", "6wb"):
            self.assertEqual(self.config(modules=[module])["modules"], [module])

    def test_invalid_module_selections_fail_validation(self):
        for modules in ("6wb", [], ["hud"], ["6wb", "6wb"], [{}]):
            with self.subTest(modules=modules), self.assertRaisesRegex(ValueError, "modules must select"):
                self.config(modules=modules)
