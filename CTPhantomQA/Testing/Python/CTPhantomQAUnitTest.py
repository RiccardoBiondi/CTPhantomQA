import sys
import types
import pytest

import numpy as np

from hypothesis import given
from hypothesis import strategies as st

from unittest.mock import patch


from pathlib import Path

from CTPhantomQA.Testing.Python.mocks import MockScalarVolumeNode
from CTPhantomQA.Testing.Python.mocks import mock_arrayFromVolume


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

        assert list(phantom.modules.keys()) == ["Test101", "Test202"]

        test_101 = phantom.modules["Test101"]
        test_202 = phantom.modules["Test202"]

        assert list(test_101.analyses.keys()) == ["hu_accuracy", "homogenity"]
        assert test_101.relative_z_offset_mm == 0.0
        assert test_101.analyses["hu_accuracy"]["roi_radius_mm"] == 5.0
        assert test_101.analyses["hu_accuracy"]["targets"] ==  {
                    "Air": {
                        "angle_deg": 0,
                        "distance_mm": 50,
                        "expected_hu": -1000,
                        "tolerance": 20
                    }
                }

        assert list(test_202.analyses.keys()) == ["homogeneity"]
        assert test_202.relative_z_offset_mm == -40.0



#
# Test Cases for the evaluation of the core engine for the QA
#

class TestHUAccuracyStrategy:

    __test__ = False

    @pytest.fixture(scope="class")
    def current_testing(self):
        from CTPhantomQA.QACore.evaluators import HUAccuracyStrategy

        return HUAccuracyStrategy

    @pytest.fixture(autouse=True, scope="class")
    def setup_mock(self):
        slicer_module = types.ModuleType("slicer") # to mock the slicer environment
        slicer_module.util = types.ModuleType("slicer.util")

        slicer_module.vtkMRMLScalarVolumeNode = MockScalarVolumeNode
        slicer_module.util.arrayFromVolume = mock_arrayFromVolume

        with patch.dict(sys.modules, {"slicer": slicer_module}):
            yield slicer_module


    @staticmethod
    def sample_ct_strategy():

        params = {
            "roi_radius_mm": 4.0,
            "targets": {
                "Air": {"angle_deg": 0.0, "distance_mm": 0.0, "expected_hu": -1000, "tolerance": 10.0}
            }
        }

        test_scan = np.zeros((50, 100, 100), dtype=np.int16)
        test_scan[25, 45:56, 45:56] = params["targets"]["Air"]["expected_hu"] + np.random.randint( - params["targets"]["Air"]["tolerance"], params["targets"]["Air"]["tolerance"], (11, 11))

        return params, test_scan


    def test_hu_for_specific_target(self, current_testing):

        params, test_scan = self.sample_ct_strategy()
        v_node = sys.modules["slicer"].vtkMRMLScalarVolumeNode(test_scan)

        hu_accuracy_strategy = current_testing()

        rerult = hu_accuracy_strategy.run(v_node=v_node, z_slice_index=0, params=params)

        assert params["targets"]["Air"]["expected_hu"] == -1000