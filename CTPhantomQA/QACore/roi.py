from abc import ABC, abstractmethod, abstractclassmethod

from typing import Dict, Any, Tuple, Type, Optional, List, Iterator


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

        self._compute_control_points()

    @property
    def control_points(self) -> List[Tuple[float, float, float]]:
        return self._control_points

    @abstractmethod
    def _compute_control_points(self):
        raise NotImplementedError

    @abstractmethod
    def update_from_control_points(self, points: List[Tuple[float, float, float]]):
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: Dict) -> "BaseROI":
        return cls(**data)


@register_roi("sphere")
class SphereROI(BaseROI):

    def __init__(self, id: str, center: Tuple[float, float, float], radius_mm: float, name: Optional[str] = None, display: Optional[Dict[str, Any]] = None):

        self.radius_mm = radius_mm
        self.display = display

        super().__init__(id=id, center=center, name=name)



    def _compute_control_points(self):

        self._control_points = [
            self.center,  #center control point
            [self.center[0] + self.radius_mm, self.center[1], self.center[2]] # surface point
        ]

    def update_from_control_points(self, points: List[Tuple[float, float, float]]):

        # TODO note that it assume that the control points are in the order indicated by the render function
        self.center = points[0]

        #now conpute (and update) the radius
        dx = points[0][0] - points[1][0]
        dy = points[0][1] - points[1][1]
        dz = points[0][2] - points[1][2]

        self.radius_mm = (dx**2 + dy**2 + dz**2) ** 0.5

        self._control_points = points


@register_roi("circle")
class CirleROI(BaseROI):

    def __init__(self, id: str, center: Tuple[float, float, float], radius_mm: float, name: Optional[str] = None, display: Dict[str, Any] = {"color": [0.0, 1.0, 0.0]}, **kwargs):
        super().__init__(id=id, center=center, name=name)

        self.radius_mm = radius_mm
        self.display = display
        

    def _compute_control_points(self):
        return None

    def update_from_control_points(self, points):
        return None



'''
@register_roi("cilinder)
class CylinderROI(BaseROI):

    def __init__(self, id: str, center: Tuple[float, float, float], radius_mm: float, height: float, name: Optional[str] = None,  display: Dict[str, Any] = {"color": [0.0, 1.0, 0.0]}, **kwargs):

        super().__init__(id=id, center=center, name=name)

        self.radius_mm = radius_mm
        self.display = display
        self.height = height


    def render(self, scene):
        
               # if already exists, get the node, ohterwise create a new one
        node = scene.AddNewNodeByClass("vtkMRMLMarkupsShapeNode", f"ROI_{self.name}") if not scene.GetFirstNodeByName(f"ROI_{self.name}") else scene.GetFirstNodeByName(f"ROI_{self.name}")

        _ = node.SetShapeName(1) #slicer.vtkMRMLMarkupsShapeNode.Ring shape -> TODO create a separated engine for the rendering and an enum to set the shape in a robust way

        centro = [0.0, 0.0, 0.0]   # Coordinate [R, A, S] in mm

        raggio = 20.0               # Raggio in mm

    # Punto 1: definisce il raggio spostandosi lungo X
    #punto_raggio = [centro[0] + raggio, centro[1], centro[2]]

    # Punto 2: definisce il piano 2D spostandosi lungo Y (mantiene Z invariata per stare sul piano assiale)
    #punto_piano = [centro[0], centro[1] + raggio, centro[2]]

    # 4. Aggiungi i 3 punti di controllo necessari
    #node.RemoveAllControlPoints()
    #node.AddControlPoint(centro)        # Punto 0: Centro
    #node.AddControlPoint(punto_raggio)  # Punto 1: Raggio
    #node.AddControlPoint(punto_piano)   # Punto 2: Orientamento del piano

    # Sblocca per generare la geometria
    #node.SetControlPointPlacementUnconstrained(True)

    ## 5. Configura il Display Node per nascondere i punti
    #displayNode = node.GetDisplayNode()
    #if displayNode:
    #    displayNode.SetGlyphScale(0.0)               # Nasconde i punti di controllo
    #    displayNode.SetPointLabelsVisibility(False)  # Nasconde le etichette
    #    displayNode.SetSelectedColor(1.0, 0.2, 0.2)  # Colore rosso
    #    displayNode.SetOpacity(0.8)

        # Here the control points, 
         
        #markups_node.RemoveAllControlPoints()
        #markups_node.AddControlPoint(list(self.center), self.id)
        
                #and now configure the disply npode to render the circle
        #        display_node = markups_node.GetDisplayNode()
                # if not exists, thenv create it!
        #        if not display_node:
        #            markups_node.CreateDefaultDisplayNodes()
        #            display_node = markups_node.GetDisplayNode()
        
                # now set the rendering characteristics:
                #   - set marker shape to circle
                #   - set the marker dimension to mm
                #   - set thediameters (2 * radius)
                #   - set visualization options
        
                #display_node.SetGlyphType(slicer.vtkMRMLMarkupsDisplayNode.Circle2D)
            #    display_node.SetGlyphType(8) # here 8 is the value of the enumr Circle2D, here introduced to avoid the import of slicer and decouple the different modules
            #    display_node.SetGlyphScaleIsAbsolute(True)
            #    display_node.SetGlyphScale(float(self.radius_mm) * 2.0)
        
                # 4. Applica le opzioni di visualizzazione dal dizionario `self.display`
            #    color = self.display["color"] 
            #    display_node.SetSelectedColor(*color)
            #    display_node.SetUnselectedColor(*color)
        
                # Dimensione e visibilità dell'etichetta testo
            #    text_scale = self.display.get("text_scale", 3.0)
            #    display_node.SetTextScale(text_scale)
            #    display_node.SetPointLabelsVisibility(True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(**data)



class BoxROI(BaseROI):

    def render(self):
        ...


class PointROI(BaseROI):

    def slicer_render(self):
        ...


class LineROI(BaseROI):

    def slicer_render(self):
        ...
'''



class ROIManager:
    """Gestisce una collezione di ROI e la loro sincronizzazione globale."""

    def __init__(self):
        self._rois: Dict[str, BaseROI] = {}

    def add_roi(self, roi: BaseROI):
        self._rois[roi.id] = roi

    def remove_roi(self, roi_id: str):
        if roi_id in self._rois:
            del self._rois[roi_id]

    def get_roi(self, roi_id: str) -> Optional[BaseROI]:
        return self._rois.get(roi_id)

    def clear(self):
        self._rois.clear()

    def __iter__(self) -> Iterator[BaseROI]:
        return iter(self._rois.values())

    def __len__(self) -> int:
        return len(self._rois)

    @classmethod
    def from_list(cls, roi_data_list: List[Dict[str, Any]]) -> "ROIManager":
        """Crea un manager popolandolo direttamente da una lista di dizionari."""
        manager = cls()
        for data in roi_data_list:
            shape_type = data.get("type", "").lower()
            if shape_type in ROI_REGISTRY:
                roi_cls = ROI_REGISTRY[shape_type]
                # Rimuove 'type' prima di passare i kwargs a from_dict
                kwargs = {k: v for k, v in data.items() if k != "type"}
                roi = roi_cls.from_dict(kwargs)
                manager.add_roi(roi)
            else:
                print(f"Warning: Tipo ROI '{shape_type}' non riconosciuto.")
        return manager