from __future__ import annotations
import slicer
import logging
from typing import TYPE_CHECKING, Dict, List, Tuple


if TYPE_CHECKING: 
    from .roi import BaseROI, ROIManager



class SlicerROIRenderer:
    """Motore esteso per il rendering singolo e batch di ROI in 3D Slicer."""

    #TODO Find a way to use the call to Enum to avoid conflicts between different versions
    SHAPE_MAPPING: Dict[str, int] = {
        "SphereROI": 0,#0,#slicer.vtkMRMLMarkupsShapeNode.Sphere,
        "CylinderROI": 4#slicer.vtkMRMLMarkupsShapeNode.Cylinder,
        "CircleROI": 4 # Consider the circle as a Cylinder with height=0
        # "RingROI": slicer.vtkMRMLMarkupsShapeNode.Ring,
    }

    def __init__(self, scene=None):
        self.scene = scene or slicer.mrmlScene
        self._rendered_nodes: Dict[str, slicer.vtkMRMLMarkupsShapeNode] = {}
        self._observers = {}

    def render_roi(self, roi: "BaseROI") -> "slicer.vtkMRMLMarkupsShapeNode":
        """Renderizza una singola ROI (metodo precedente)."""
        node_name = f"ROI_{roi.name}"
        node = self.scene.GetFirstNodeByName(node_name)
        
        if not node:
            node = self.scene.AddNewNodeByClass("vtkMRMLMarkupsShapeNode", node_name)
            node.CreateDefaultDisplayNodes()

        class_name = roi.__class__.__name__
        logging.debug(f"Shape Class Name: {class_name}")
        logging.debug(f"Available Shapes: {self.SHAPE_MAPPING.keys()}")
        if class_name in list(self.SHAPE_MAPPING.keys()):
            node.SetShapeName(self.SHAPE_MAPPING[class_name])

        # Batch update dei punti senza scatenare troppi eventi
        was_modifying = node.StartModify()
        node.RemoveAllControlPoints()
        for i, pt in enumerate(roi.control_points):
            node.AddControlPoint(list(pt), f"P{i}")

        # TODO if not side effects, remove the comment below
        # node.SetControlPointPlacementUnconstrained(True)
        node.EndModify(was_modifying)

        self._apply_display_style(node, roi.display)
        self._bind_interactivity(node, roi)

        self._rendered_nodes[roi.id] = node
        return node

    def render_all(self, manager, cleanup_orphans: bool = True):
            """Renderizza tutte le ROI gestite dal manager in un unico blocco ottimizzato."""
            active_ids = set()

            for roi in manager:
                self.render_roi(roi)
                active_ids.add(roi.id)

            # Pulizia nodi rimossi (orphans)
            if cleanup_orphans:
                orphaned_ids = set(self._rendered_nodes.keys()) - active_ids
                for roi_id in orphaned_ids:
                    node = self._rendered_nodes.pop(roi_id, None)
                    if node:
                        # Rimuovi observer se presente prima di rimuovere il nodo
                        if node in self._observers:
                            tag = self._observers.pop(node)
                            if node.HasObserver(tag):  # Controlla se l'observer esiste
                                node.RemoveObserver(tag)

                        self.scene.RemoveNode(node)

    def _apply_display_style(self, node, display_config: Dict):
        display_node = node.GetDisplayNode()
        if not display_node:
            return

        color = display_config.get("color", [0.0, 1.0, 0.0])
        opacity = display_config.get("opacity", 0.7)
        show_points = display_config.get("show_control_points", False)

        display_node.SetSelectedColor(*color)
        display_node.SetOpacity(opacity)
        
        if not show_points:
            display_node.SetGlyphScale(0.0)
            display_node.SetPointLabelsVisibility(False)

    def _bind_interactivity(self, node, roi):
            def on_point_modified(caller, event):
                pts = []
                for i in range(caller.GetNumberOfControlPoints()):
                    pos = [0.0, 0.0, 0.0]
                    caller.GetNthControlPointPosition(i, pos)
                    pts.append(tuple(pos))
                roi.update_from_control_points(pts)

            # 1. Se il nodo ha già un observer registrato, rimuovilo usando il TAG corretto
            if node in self._observers:
                old_tag = self._observers.pop(node)
                if node.HasObserver(old_tag):
                    node.RemoveObserver(old_tag)

            # 2. Aggiungi il nuovo observer e salva il TAG restituito
            observer_tag = node.AddObserver(
                slicer.vtkMRMLMarkupsNode.PointModifiedEvent, on_point_modified
            )
            self._observers[node] = observer_tag