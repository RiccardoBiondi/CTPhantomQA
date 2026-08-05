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

        assert len(phantom.modules) == 2

        test_101 = phantom.modules[0]
        test_202 = phantom.modules[1]

        assert test_101.name == "Test101"
        assert test_101.analysis_type == "hu_accuracy"
        assert test_101.relative_z_offset_mm == 0.0
        assert test_101.parameters["roi_radius_mm"] == 5.0
        assert test_101.parameters["targets"] ==  {
                    "Air": {
                        "angle_deg": 0,
                        "distance_mm": 50,
                        "expected_hu": -1000,
                        "tolerance": 20
                    }
                }

        assert test_202.name == "Test202"
        assert test_202.analysis_type == "homogeneity"
        assert test_202.relative_z_offset_mm == -40.0
        assert test_202.parameters["expected_hu"] == 0
        assert test_202.parameters["tolerance"] == 5
