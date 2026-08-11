import slicer

import slicer

class SlicerROIRenderer:
    """Motore esteso per il rendering singolo e batch di ROI in 3D Slicer."""

    SHAPE_MAPPING = {
        "SphereROI": slicer.vtkMRMLMarkupsShapeNode.Sphere,
        "CylinderROI": slicer.vtkMRMLMarkupsShapeNode.Cylinder,
        # "RingROI": slicer.vtkMRMLMarkupsShapeNode.Ring,
    }

    def __init__(self, scene=None):
        self.scene = scene or slicer.mrmlScene
        self._rendered_nodes: Dict[str, slicer.vtkMRMLMarkupsShapeNode] = {}
        self._observers = {}

    def render_roi(self, roi: BaseROI) -> slicer.vtkMRMLMarkupsShapeNode:
        """Renderizza una singola ROI (metodo precedente)."""
        node_name = f"ROI_{roi.name}"
        node = self.scene.GetFirstNodeByName(node_name)
        
        if not node:
            node = self.scene.AddNewNodeByClass("vtkMRMLMarkupsShapeNode", node_name)
            node.CreateDefaultDisplayNodes()

        class_name = roi.__class__.__name__
        if class_name in self.SHAPE_MAPPING:
            node.SetShapeName(self.SHAPE_MAPPING[class_name])

        # Batch update dei punti senza scatenare troppi eventi
        was_modifying = node.StartModify()
        node.RemoveAllControlPoints()
        for i, pt in enumerate(roi.get_control_points()):
            node.AddControlPoint(list(pt), f"P{i}")

        node.SetControlPointPlacementUnconstrained(True)
        node.EndModify(was_modifying)

        self._apply_display_style(node, roi.display)
        self._bind_interactivity(node, roi)

        self._rendered_nodes[roi.id] = node
        return node

    def render_all(self, manager: ROIManager, cleanup_orphans: bool = True):
        """Renderizza tutte le ROI gestite dal manager in un unico blocco ottimizzato."""
        
        # 1. Disabilita temporaneamente il rendering 3D per performance durante il caricamento massivo
        # (particolarmente utile quando si caricano decine o centinaia di ROI)
        active_ids = set()

        for roi in manager:
            self.render_roi(roi)
            active_ids.add(roi.id)

        # 2. Pulizia automatica: rimuove da Slicer i nodi le cui ROI sono state cancellate dal Manager
        if cleanup_orphans:
            orphaned_ids = set(self._rendered_nodes.keys()) - active_ids
            for roi_id in orphaned_ids:
                node = self._rendered_nodes.pop(roi_id, None)
                if node:
                    if node in self._observers:
                        node.RemoveObserver(self._observers.pop(node))
                    self.scene.RemoveNode(node)

    def _apply_display_style(self, node, display_config: dict):
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

    def _bind_interactivity(self, node, roi: BaseROI):
        def on_point_modified(caller, event):
            pts = []
            for i in range(caller.GetNumberOfControlPoints()):
                pos = [0.0, 0.0, 0.0]
                caller.GetNthControlPointPosition(i, pos)
                pts.append(tuple(pos))
            roi.update_from_control_points(pts)

        if node in self._observers:
            node.RemoveObserver(self._observers[node])

        observer_tag = node.AddObserver(slicer.vtkMRMLMarkupsNode.PointModifiedEvent, on_point_modified)
        self._observers[node] = observer_tag