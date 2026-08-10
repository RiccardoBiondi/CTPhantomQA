from abc import ABC, abstractmethod, abstractclassmethod

from typing import Dict, Any, Tuple, Type, Optional


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

    def __init__(self, id: str, center: Tuple[float, float, float], name: Optional[str] = None): 
        self.id = id
        self.center = center
        self.name  = name if name is not None else id
    @abstractmethod
    def slice_render(self):
        raise NotImplementedError

    @abstractclassmethod
    def from_dict(self, data: Dict) -> "BaseROI":
        raise NotImplementedError


class CirleROI(BaseROI):

    def __init__(self, id: str, center: Tuple[float, float, float], radius_mm: float, name: Optional[str] = None, display: Dict[str, Any] = {"color": [0.0, 1.0, 0.0]}, **kwargs):
        super().__init__(id=id, center=center, name=name)

        self.radius_mm = radius_mm
        self.display = display
        

    def slice_render(self, scene):

        import slicer
        # if already exists, get the node, ohterwise create a new one
        markups_node = scene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", f"ROI_{self.name}") if not scene.GetFirstNodeByName(f"ROI_{self.name}") else scene.GetFirstNodeByName(f"ROI_{self.name}")

        # now set/ update tghe node position (given by the center)

        markups_node.RemoveAllControlPoints()
        markups_node.AddControlPoint(list(self.center), self.id)

        #and now configure the disply npode to render the circle
        display_node = markups_node.GetDisplayNode()
        # if not exists, thenv create it!
        if not display_node:
            markups_node.CreateDefaultDisplayNodes()
            display_node = markups_node.GetDisplayNode()

        # now set the rendering characteristics:
        #   - set marker shape to circle
        #   - set the marker dimension to mm
        #   - set thediameters (2 * radius)
        #   - set visualization options

        display_node.SetGlyphType(slicer.vtkMRMLMarkupsDisplayNode.Circle2)
        display_node.SetGlyphScaleIsAbsolute(True)
        display_node.SetGlyphScale(float(self.radius_mm) * 2.0)

        # 4. Applica le opzioni di visualizzazione dal dizionario `self.display`
        color = self.display["color"] 
        display_node.SetSelectedColor(*color)
        display_node.SetUnselectedColor(*color)

        # Dimensione e visibilità dell'etichetta testo
        text_scale = self.display.get("text_scale", 3.0)
        display_node.SetTextScale(text_scale)
        display_node.SetPointLabelsVisibility(True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BaseROI:
        return cls(**data)



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
