import sys
import types
import numpy as np
import pytest

# --- 1. CONFIGURAZIONE DEL MOCK DI SLICER ---
# Creiamo un modulo finto 'slicer' nella memoria di Python prima di importare gli evaluators
mock_slicer = types.ModuleType("slicer")
mock_slicer.util = types.ModuleType("slicer.util")

# Simuliamo una matrice VTK minimale per non far crashare il codice
class MockMatrix4x4:
    def MultiplyPoint(self, point_ras):
        # In un test controllato, possiamo fare in modo che restituisca 
        # direttamente indici mappati 1:1 o applicare una traslazione fissa
        # Es: RAS [10, 20, 30, 1] -> IJK [10, 20, 30, 1] (moltiplicazione per identità)
        return point_ras

class MockScalarVolumeNode:
    def __init__(self, fake_array):
        self.fake_array = fake_array

    def GetSpacing(self):
        # Restituisce lo spacing (X, Y, Z) in mm
        return (0.5, 0.5, 1.0)

    def GetRASToIJKMatrix(self, matrix=None):
        # Se la tua strategia richiede di passare una matrice pre-creata
        if matrix is not None:
            return matrix
        return MockMatrix4x4()

# Definiamo la funzione finta arrayFromVolume
def fake_array_from_volume(volume_node):
    return volume_node.fake_array

# Iniettiamo le funzioni nel mock
mock_slicer.util.arrayFromVolume = fake_array_from_volume
mock_slicer.vtkMRMLScalarVolumeNode = MockScalarVolumeNode

# Inseriamo il finto modulo in sys.modules così che 'import slicer' funzioni ovunque
sys.modules["slicer"] = mock_slicer
# Facciamo lo stesso per vtk se usato nel codice
sys.modules["vtk"] = types.ModuleType("vtk") 

# --- 2. IL TEST VERO E PROPRIO ---
# Ora possiamo importare la strategia in modo sicuro fuori da Slicer
from QACore.evaluators import HUAccuracyStrategy

def test_hu_accuracy_with_mock():
    # Crea un fantoccio finto (array 3D 100x100x100) pieno di acrilico (es: valore 120 HU)
    fake_ct_scan = np.full((100, 100, 100), 120, dtype=np.int16)
    
    # Disegniamo un inserto di "Aria" (-1000 HU) in una coordinata specifica per il test
    # Supponiamo che la coordinata pixel calcolata dalla strategia cada a Y=50, X=50 sulla fetta Z=10
    fake_ct_scan[10, 45:55, 45:55] = -1000 
    
    # Istanziamo il nostro volume mockato
    v_node_mock = MockScalarVolumeNode(fake_ct_scan)
    
    # Definiamo dei parametri JSON finti che puntano a quella zona
    fake_params = {
        "roi_radius_mm": 2.5, # Con spacing 0.5mm significa 5 pixel di raggio
        "targets": {
            "Air_Test": {
                "angle_deg": 0.0,      # Gestisci la trigonometria nel mock in modo che
                "distance_mm": 0.0,    # cada esattamente al centro (50, 50) per semplicità
                "expected_hu": -1000.0,
                "tolerance": 10.0
            }
        }
    }
    
    # Inizializziamo ed eseguiamo la strategia
    strategy = HUAccuracyStrategy()
    
    # Modifica momentaneamente il metodo della strategia per forzare il centro del fantoccio
    # in modo che la trigonometria punti al pixel (50,50)
    strategy.get_phantom_center_ras = lambda: [50.0, 50.0, 10.0]
    
    results = strategy.run(v_node=v_node_mock, z_slice_index=10, params=fake_params)
    
    # --- ASSERZIONI SU NUMPY ---
    assert results["Air_Test"]["passed"] is True
    assert results["Air_Test"]["measured_hu"] == -1000.0
    assert results["Air_Test"]["noise"] == 0.0  # Tutti i pixel della ROI sono identici a -1000
