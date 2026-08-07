from abc import ABC, abstractmethod, abstractclassmethod

from typing import Dict, Any, Tuple, Type


__author__ = ["Riccardo Biondi"]
__email__ = ["riccardo.biondi@proton.me"]

ROI_REGISTRY: Dict[str, Type["BaseROI"]] = {}

def register_roi(shape_name: str):
    """Decoratore per registrare automaticamente una classe ROI nel Registry."""
    def decorator(cls: Type["BaseROI"]):
        ROI_REGISTRY[shape_name.lower()] = cls
        return cls
    return decorator


class BaseROI(ABC):

    def __init__(self, roi_id: str, center: Tuple[float, float, float], purpose: str): 
        self.roi_id = roi_id
        self.center = center
        self.purpose = purpose # pensa bene a come effettivamente andrebbe inizializzato

    @abstractmethod
    def slice_render(self):
        raise NotImplementedError

    @abstractclassmethod
    def from_dict(self, data: Dict) -> "BaseROI":
        raise NotImplementedError


class CirleROI(BaseROI):

    def __init__(self, roi_id: str, center: Tuple[float, float, float], purpose: str, radius_mm: float):
        super().__init__(roi_id=roi_id, center=center, purpose=purpose)

        self.radius_mm = radius_mm
        

    def slice_render(self):
        return super().slice_render()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BaseROI:
        ...
        #return cls()



class CylinderROI(BaseROI):

    def slice_render(self):
        return super().slice_render()


class BoxROI(BaseROI):

    def slice_render(self):
        return super().slice_render()


class PointROI(BaseROI):

    def slice_render(self):
        return super().slice_render()


class LineROI(BaseROI):

    def slice_render(self):
        return super().slice_render()
