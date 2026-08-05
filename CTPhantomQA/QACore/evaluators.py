from abc import ABC, abstractclassmethod
import numpy as np

from typing import Dict, Any
from numpy.typing import NDArray


__author__ = ["Riccardo Biondi"]
__email__ = ["riccardo.biondi@proton.me"]


#
# Implementation of the different analysis strategies for the different scenarios (hu, linearity, thickness, etc.)
#

class BaseAnalysisStrategy(ABC):

    @abstractmethod
    def run(self, volume_array: NDArray, z_slice_index: int, v_node, params: Dict[str, Any]) -> Dict:
       ...


class HUAccuracyStrategy(BaseAnalysisStrategy):

    def run(self, volume_array: NDArray, z_slice_index: int, v_node, params: Dict[str, Any]) -> Dict:
        ...


class SliceThicknessStrategy(BaseAnalysisStrategy):

    def run(self, volume_array: NDArray, z_slice_index: int, v_node, params: Dict[str, Any]) -> Dict:
        ...

class HomogeneityUniformityStrategy(ABC):

    def run(self, volume_array: NDArray, z_slice_index: int, v_node, params: Dict[str, Any]) -> Dict:
        ...

class SpatialResolutionMTFStrategy(ABC):

    def run(self, volume_array: NDArray, z_slice_index: int, v_node, params: Dict[str, Any]) -> Dict:
        ...


class AnalysisFactory:
    _strategies = {
        "hu_accuracy": HUAccuracyStrategy,
        "slice_thickness": SliceThicknessStrategy,
        "homogeneity": HomogeneityUniformityStrategy,
        "spatial_resolution": SpatialResolutionMTFStrategy
    }