import pytest

from hypothesis import given
from hypothesis import strategies as st

from pathlib import Path


__author__ = ["Riccardo Biondi"]
__email__ = ["riccardo.biondi@proton.me"]


class TestConfigParser:

    __test__ = True

    @pytest.fixture(scope="class")
    def json_path(self) -> Path:
        return Path(".") / "CTPhantomQA" / "Resources" / "Phantoms" / "phantom_test.json"


    @pytest.fixture(scope="class")
    def current_testing(self):
        from CTPhantomQA.QACore.config_parser import PhantomConfig

        return PhantomConfig


    def test_phantom_config_loading(self, json_path: Path, current_testing):
        r"""
        """
        # read the phantom from the configuration file

        phantom = current_testing.from_json(json_path)
        modules = phantom.modules
        assert phantom.phantom_name == "TestPhantom"
        assert list(modules.keys()) == ["Test101", "Test202"]

        assert modules["Test101"].relative_z_offset_mm == 0
        assert modules["Test202"].relative_z_offset_mm == -40

        assert list(modules["Test101"].targets.keys()) == ["Air", "Teflon", "Acrylic"]

        assert modules["Test101"].targets["Air"].angle_deg == 0
        assert modules["Test101"].targets["Air"].distance_mm == 50
        assert modules["Test101"].targets["Air"].expected_hu == -1000
        assert modules["Test101"].targets["Air"].tolerance == 20
