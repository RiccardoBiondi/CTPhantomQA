import sys
import types
import numpy as np
import pytest
from typing import Tuple, List, NoReturn, Optional

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

    def GetRASTOIJKMatrix(self, matrix = None):
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


