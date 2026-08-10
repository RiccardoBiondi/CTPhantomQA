import sys
import types
import numpy as np
import pytest
from typing import Tuple, List, NoReturn, Optional, Dict

# --- 1. CONFIGURAZIONE DEL MOCK DI SLICER ---
# Creiamo un modulo finto 'slicer' nella memoria di Python prima di importare gli evaluators
mock_slicer = types.ModuleType("slicer")
mock_slicer.util = types.ModuleType("slicer.util")


class MockMatrix4x4:
    def MultiplyPoint(self, point_ras):
        return point_ras


class MockScalarVolumeNode:

    def __init__(self, array: np.typing.NDArray, spacing: Tuple[float, float, float] = (1., 1., 1.), origin_ras: Tuple[float, float, float] = (0., 0., 0.)):

        self.array = array
        self._spacing = spacing
        self._origin_ras = origin_ras

    def GetSpacing(self) -> Tuple[float, float, float]:
        return self._spacing

    def GetOrigin(self) -> Tuple[float, float, float]: 
        return self._origin_ras

    def GetRASToIJKMatrix(self, matrix = None):
        if matrix is not None:
            return matrix
        return MockMatrix4x4()

    def GetRASBounds(self, bound_list: List[float]) -> NoReturn:

        z, y, x = self.array.shape

        # R (x) min and max
        bound_list[0] = self._origin_ras[0]
        bound_list[1] = self._origin_ras[0] + (x * self._spacing[0])

        #A (y) min and max
        bound_list[2] = self._origin_ras[1]
        bound_list[3] = self._origin_ras[1] + (y * self._spacing[1])

        # S (z) min and max
        bound_list[4] = self._origin_ras[2]
        bound_list[5] = self._origin_ras[2] + (z * self._spacing[2])


def mock_arrayFromVolume(v_node) -> np.typing.NDArray:

    return v_node.array


class MockDisplayNode:

    def __init__(self):

        self.gliph_type = None
        self.gliph_scale_is_absolute: bool = False
        self.gliph_scale = 0.0

        self.selected_color: Optional[Tuple[float, float, float]] = None
        self.unselected_color: Optional[Tuple[float, float, float]] = None

        self.text_scale: float = 1.0
        self.point_label_visibility: bool = False


    def SetGlyphType(self, gliph_type):
        self.gliph_type = gliph_type

    def GetGliphType(self): 
        return self.gliph_type

    def SetGlyphScaleIsAbsolute(self, flag: bool):
        self.gliph_scale_is_absolute = flag

    def GetGlyphScaleIsAbsolute(self) -> bool: 
        return self.gliph_scale_is_absolute


    def SetGlyphScale(self, scale: float):
        self.gliph_scale = scale

    def GetGlyphScale(self): 
        return self.gliph_scale

    def SetSelectedColor(self, R: float, G: float, B: float):
        self.selected_color = (R, G, B)

    def GetSelectedColor(self) -> Tuple[float, float, float]:
        return self.selected_color


    def SetUnselectedColor(self, R: float, G: float, B: float): 
        self.unselected_color = (R, G, B)

    def GetUnselectedColor(self) -> Tuple[float, float, float]:
        return self.unselected_color

    def SetTextScale(self, scale: float):
        self.text_scale = scale

    def GetTextScale(self) -> float:
        return self.text_scale        

    def SetPointLabelsVisibility(self, visibility: bool):
        self.point_label_visibility = visibility

    def GetPointLabelsVisibility(self) -> bool:
        return self.point_label_visibility


class MockMarkupFiducialNode:

    def __init__(self):

        self.display_node: Optional[MockDisplayNode] = None
        self.control_points: Dict[str, List[float]] = {}

    def CreateDefaultDisplayNodes(self):

        self.display_node = MockDisplayNode()

    def GetDisplayNode(self):
        return self.display_node

    def AddControlPoint(self, center: List[float], id: str) -> None:

        self.control_points.update({id: center})

    def RemoveAllControlPoints(self): 
        self.control_points = {}


class MockSlicerScene:

    def __init__(self):

        self.scene = None

        self.nodes: Dict[str, MockMarkupFiducialNode] = {}



        #self.control_points: Dict[str, List[float]] = {}

        #self.display_node: Optional[MockDisplayNode] = None

    def AddNewNodeByClass(self, class_name: str, label: str):

        if label not in list(self.nodes.keys()):
            self.nodes.update({label : MockMarkupFiducialNode()})

        return self.nodes[label]

    def GetFirstNodeByName(self, label: str):
        return self.nodes.get(label, None)

