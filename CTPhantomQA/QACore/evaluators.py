from abc import ABC, abstractclassmethod
import numpy as np

from typing import Dict, Any
from numpy.typing import NDArray


__author__ = ["Riccardo Biondi"]
__email__ = ["riccardo.biondi@proton.me"]

# TODO think about the registry pattern to easily add custom analysis classes


#
# Implementation of the different analysis strategies for the different scenarios (hu, linearity, thickness, etc.)
#

class BaseAnalysisStrategy(ABC):

    @abstractmethod
    def run(self, v_node, z_slice_index: int, params: Dict[str, Any]) -> Dict:
       raise NotImplementedError


class HUAccuracyStrategy(BaseAnalysisStrategy):

    def run(self,  v_node, z_slice_index: int, params: Dict[str, Any]) -> Dict:
        ...


class SliceThicknessStrategy(BaseAnalysisStrategy):

    def run(self,  v_node, z_slice_index: int, params: Dict[str, Any]) -> Dict:
        ...

class HomogeneityUniformityStrategy(ABC):

    def run(self,  v_node, z_slice_index: int, params: Dict[str, Any]) -> Dict:
        ...

class SpatialResolutionMTFStrategy(ABC):

    def run(self,  v_node, z_slice_index: int, params: Dict[str, Any]) -> Dict:
        ...


class AnalysisFactory:
    _strategies = {
        "hu_accuracy": HUAccuracyStrategy,
        "slice_thickness": SliceThicknessStrategy,
        "homogeneity": HomogeneityUniformityStrategy,
        "spatial_resolution": SpatialResolutionMTFStrategy
    }




    r"""
    
    class HUAccuracyStrategy(BaseAnalysisStrategy):

    Strategia per il calcolo dell'accuratezza HU.
    Trova la fetta corretta, calcola le posizioni geometriche delle ROI
    e ne estrae i dati statistici.
    
    def run(self, volume_array, z_slice_index, v_node, params) -> dict:
        # 1. INIZIALIZZAZIONE PARAMETRI
        # Recupera il raggio della ROI (convertito in mm se necessario)
        roi_radius_mm = params.get("roi_radius_mm", 5.0)
        targets_config = params.get("targets", {})
        
        # Recupera la matrice di conversione geometrica di Slicer
        ras_to_ijk_matrix = v_node.GetRASToIJKMatrix()
        pixel_spacing = v_node.GetSpacing() # Es: (0.5mm, 0.5mm, 1.0mm)
        
        # Identifica il centro del fantoccio nello spazio millimetrico (RAS)
        # Nota: assumiamo che il centro sia stato calcolato o passato dall'evaluatore
        phantom_center_ras = self.get_phantom_center_ras() 
        z_center_ras = phantom_center_ras[2]
        
        results = {}
        
        # 2. IDENTIFICAZIONE DELLA FETTA CORRETTA
        # Nota: in NumPy la prima coordinata è la fetta Z (K)
        # Estraiamo la singola matrice 2D per velocizzare i calcoli
        slice_2d = volume_array[z_slice_index, :, :]

        # 3. LOOP SU TUTTI I TARGET DEL MATERIALE (Aria, Teflon, ecc.)
        for target_name, target in targets_config.items():
            
            # --- Calcolo Trigonometrico della Posizione della ROI (In Millimetri) ---
            # Converte l'angolo del JSON in radianti
            angle_rad = math.radians(target.angle_deg)
            
            # Calcola le coordinate X(R) e Y(A) della ROI nello spazio fisico mm
            roi_r_mm = phantom_center_ras[0] + (target.distance_mm * math.cos(angle_rad))
            roi_a_mm = phantom_center_ras[1] + (target.distance_mm * math.sin(angle_rad))
            
            # --- Conversione da mm a Pixel (Spazio IJK di Slicer) ---
            point_ras = [roi_r_mm, roi_a_mm, z_center_ras, 1.0]
            point_ijk = ras_to_ijk_matrix.MultiplyPoint(point_ras)
            
            # Arrotonda per trovare il pixel centrale della ROI nella matrice
            center_i = int(round(point_ijk[0])) # Indice colonna (X)
            center_j = int(round(point_ijk[1])) # Indice riga (Y)
            
            # --- Estrazione della Maschera della ROI Circolare (Stile Pylinac) ---
            # Calcola il raggio della ROI convertito in numero di pixel
            # Pylinac usa una maschera circolare esatta, non un quadrato
            radius_in_pixels = roi_radius_mm / pixel_spacing[0]
            
            # Definisce un bounding box quadrato attorno al centro per ottimizzare la ricerca
            i_min = int(center_i - radius_in_pixels)
            i_max = int(center_i + radius_in_pixels)
            j_min = int(center_j - radius_in_pixels)
            j_max = int(center_j + radius_in_pixels)
            
            # Estrae la sotto-matrice quadrata
            sub_grid = slice_2d[j_min:j_max+1, i_min:i_max+1]
            
            # Crea una griglia di coordinate relative all'interno del bounding box
            y_indices, x_indices = np.ogrid[j_min:j_max+1, i_min:i_max+1]
            
            # Formula del cerchio: (x - x_centro)^2 + (y - y_centro)^2 <= raggio^2
            distance_from_center_squared = (x_indices - center_i)**2 + (y_indices - center_j)**2
            circular_mask = distance_from_center_squared <= radius_in_pixels**2
            
            # Estrae solo i pixel che cadono dentro il cerchio perfetto
            roi_pixels = sub_grid[circular_mask]
            
            # 4. CALCOLO DELLE METRICHE STATISTICHE
            if roi_pixels.size == 0:
                continue # Salta se la ROI è fuori dall'immagine
                
            mean_hu = float(np.mean(roi_pixels))   # Media HU (Accuratezza)
            std_hu = float(np.std(roi_pixels))     # Deviazione Standard (Rumore dell'inserto)
            
            # Verifica dei criteri di tolleranza clinica
            deviation = mean_hu - target.expected_hu
            passed = abs(deviation) <= target.tolerance
            
            # 5. SALVATAGGIO DEI DATI
            results[target_name] = {
                "measured_hu": mean_hu,
                "noise": std_hu,
                "expected_hu": target.expected_hu,
                "deviation": deviation,
                "passed": passed,
                "center_pixel_ij": (center_i, center_j),
                "center_ras_mm": (roi_r_mm, roi_a_mm, z_center_ras)
            }
            
        return results

    """