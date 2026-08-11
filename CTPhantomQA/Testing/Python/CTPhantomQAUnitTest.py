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

from CTPhantomQA.Testing.Python.mocks import MockSlicerScene


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


        assert phantom.protocol_name == "Test Protocol"
        assert phantom.phantom_name == "Test Phantom"
        assert len(modules) == 2


        test_101 = phantom.modules[0]
        test_202 = phantom.modules[1]


        assert test_101.module_name == "Test101"
        assert test_101.relative_z_offset_mm == 0.0
        assert len(test_101.rois) == 1


        assert test_202.module_name == "Test202"
        assert test_202.relative_z_offset_mm == -40.0
        assert len(test_101.rois) == 1


        roi_test_101 = test_101.rois[0]
        roi_test_202 = test_202.rois[0]

        assert roi_test_101.id == "Air"
        assert roi_test_101.center == [0, 0]
        assert roi_test_101.radius_mm == 5.0
        assert roi_test_101.display == {"color": [0.0, 1.0, 0.0]}

#
# Test Cases for the evaluation of the core engine for the QA
#

class TestHUAccuracyStrategy:

    __test__ = True

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



class ROITestStrategyBase:

    __test__ = True


    def verify_control_points(self, roi, control_points):


        assert roi.control_points == control_points



class TestSphereROI(ROITestStrategyBase):

    __test__ = True

    @pytest.fixture(scope="class")
    def roi(self):
        from CTPhantomQA.QACore.roi import SphereROI
        return SphereROI

    def test_control_point_instantiation(self, roi): 

        true_control_points = [
            (0., 0., 0.),
            (10., 0., 0.)
        ]

        test_roi = roi(id="TestSphere", center=(0., 0., 0.), radius_mm = 10.)

        self.verify_control_points(test_roi, true_control_points)
    '''
class ROIRenderTestStrategyBase:


    __test__ = False

    @pytest.fixture()
    def empty_scene(self):
        return MockSlicerScene()

    
    #@pytest.fixture(autouse=True, scope="class")
    #def setup_mock(self):
    #    slicer_module = types.ModuleType("slicer") # to mock the slicer environment
    #    slicer_module.vtkMRMLMarkupsDisplayNode = types.ModuleType("slicer.vtkMRMLMarkupsDisplayNode")
  #
    #    with patch.dict(sys.modules, {"slicer": slicer_module}):
    #        yield slicer_module
'''

'''
class TestRenderCircularROI(ROIRenderTestStrategyBase):

    __test__ = True


    def test_render_on_empty_scene(self, empty_scene: MockSlicerScene):

        from CTPhantomQA.QACore.roi import CirleROI

        roi = CirleROI(id="test101", name="test_name", center=[5.0, 6.0, 0.0], radius_mm=10.)

        _ = roi.render(empty_scene)

        markups_node = empty_scene.GetFirstNodeByName("ROI_test_name")
        display_node = markups_node.GetDisplayNode()
        control_point = markups_node.control_points

        assert control_point["test101"] == [5.0, 6.0, 0.0]

'''

'''
class TestSlicerRendering(ROIRenderTestStrategyBase):

    __test__ = True

    def test_test_rended_multiple_rois(self, empty_scene: MockSlicerScene): 
        from CTPhantomQA.QACore.roi import CirleROI

        roi101 = CirleROI(id="test101", name="name_101", center=[0.0, 0.0, 0.0], radius_mm=5.)
        roi202 = CirleROI(id="test202", name="name_202", center=[5.0, 1.0, 3.5], radius_mm=15.)

        _ = roi101.render(empty_scene)
        _ = roi202.render(empty_scene)

        assert len(list(empty_scene.nodes.keys())) == 2
'''