import logging
import os
import json
import glob
from typing import Annotated

import vtk

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode

from pathlib import Path
#
# test
#
from QACore.config_parser import PhantomConfig


class CTPhantomQA(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("CTPhantomQA") 
        #self.parent.categories = [translate("Radiology")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Riccardo Biondi"]  # TODO: replace with "Firstname Lastname (Organization)"

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """Add data sets to Sample Data module."""
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # test1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="test",
        sampleName="test1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "test1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="test1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="test1",
    )

    # test2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="test",
        sampleName="test2",
        thumbnailFileName=os.path.join(iconsPath, "test2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="test2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="test2",
    )


#
# testParameterNode
#


@parameterNodeWrapper
class CTPhantomQAParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """

    inputVolume: vtkMRMLScalarVolumeNode
    selectedConfigurationFile: Path
    #outputTableNode: vtkMRMLTableNode
    #roiMarkupsNode: vtkMRMLMarkupsFiducialNode # Phantom ROI points to plot on the volume


class CTPhantomQAWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/CTPhantomQA.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = CTPhantomQALogic()


        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # Buttons
        self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()
        self.populateJsonComboBox()


    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()
        self.populateJsonComboBox()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()
            self.populateJsonComboBox()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored
        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode

    def setParameterNode(self, inputParameterNode: CTPhantomQAParameterNode | None) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()

    def populateJsonComboBox(self):
        """Scansiona la cartella delle configurazioni JSON e popola la QComboBox."""
        
        # 1. Blocco temporaneo dei segnali per evitare che scattino eventi durante il caricamento
        wasBlocking = self.ui.jsonSelectorComboBox.blockSignals(True)
        self.ui.jsonSelectorComboBox.clear()

        # 2. Definisci il percorso dove risiedono i file JSON (es. la cartella Resources/Configs del modulo)
        configsDir = self.resourcePath("Configs")  # Oppure os.path.join(os.path.dirname(__file__), "Resources/Configs")
        configsDir = os.path.join(os.path.dirname(__file__), "Resources/Phantoms")
        
        if not os.path.exists(configsDir):
            os.makedirs(configsDir)
            logging.warning(f"Cartella configurazioni creata: {configsDir}")

        # 3. Trova tutti i file .json nella cartella
        jsonFiles = glob.glob(os.path.join(configsDir, "*.json"))

        if not jsonFiles:
            self.ui.jsonSelectorComboBox.addItem("Nessuna configurazione trovata", None)
            self.ui.jsonSelectorComboBox.blockSignals(wasBlocking)
            return

        # 4. Popola la ComboBox
        for jsonPath in jsonFiles:
            try:
                configData = PhantomConfig.from_json(jsonPath)
                    
                # Cerca un titolo formale nel JSON, altrimenti usa il nome del file
                displayName = configData.phantom_name
                
                # addItem(testo_visibile, valore_nascosto_userData)
                self.ui.jsonSelectorComboBox.addItem(displayName, jsonPath)

            except Exception as e:
                logging.error(f"Errore nel caricamento del file JSON {jsonPath}: {e}")

        # 5. Ripristina i segnali ed emetti l'evento per la prima selezione
        self.ui.jsonSelectorComboBox.blockSignals(wasBlocking)
        self.onJsonSelectionChanged()

    def onJsonSelectionChanged(self):

        """Gestisce l'evento di cambio di selezione del file JSON."""
        comboBox = self.ui.jsonSelectorComboBox

        # 1. Recupera l'indice dell'elemento attualmente selezionato
        currentIndex = comboBox.currentIndex

        if currentIndex < 0:
            return

        # 2. Usa itemData(index) invece di currentData()
        selectedJsonPath = comboBox.itemData(currentIndex)

        if selectedJsonPath and os.path.exists(selectedJsonPath):
            # Aggiorna il ParameterNode se disponibile
            if self._parameterNode:
                self._parameterNode.selectedConfigurationFile = Path(selectedJsonPath)

            logging.info(f"Configurazione selezionata: {selectedJsonPath}")
        configData = PhantomConfig.from_json(selectedJsonPath)

        self.updateConfigInfoDisplay(configData)

    def updateConfigInfoDisplay(self, configData: PhantomConfig):
        r"""
        Construct and HTML formatted reporting the selected configuration parameters
        """

        html = f"<h3>Ciaoooooooo</h3>"
        html += f"<b>Phantom:</b> {configData.phantom_name}<br><br>"

    # Aggiorna il widget QTextEdit
        self.ui.configurationSummary.setHtml(html)

        # configurationSummary
        ...

    def _checkCanApply(self, caller=None, event=None) -> None:
        ...
        
    def onApplyButton(self) -> None:
        """Run processing when user clicks "Apply" button."""
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            # Compute output
            self.logic.process(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(),
                               self.ui.imageThresholdSliderWidget.value, self.ui.invertOutputCheckBox.checked)

            # Compute inverted output (if needed)
            if self.ui.invertedOutputSelector.currentNode():
                # If additional output volume is selected then result with inverted threshold is written there
                self.logic.process(self.ui.inputSelector.currentNode(), self.ui.invertedOutputSelector.currentNode(),
                                   self.ui.imageThresholdSliderWidget.value, not self.ui.invertOutputCheckBox.checked, showResult=False)


#
# testLogic
#


class CTPhantomQALogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return CTPhantomQAParameterNode(super().getParameterNode())

    def process(self,
                inputVolume: vtkMRMLScalarVolumeNode,
                selectedConfigurationFile: Path
                ) -> None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        """
        ...

    def plotLandmarksFromConfig(self, configData: dict) -> None:
        ...
        """Crea o aggiorna un nodo Markups nella scena con i landmark definiti nel JSON."""

        #    node_name = "Phantom_Landmarks_Config"
#
        #    # Cerca se il nodo esiste già per non duplicarlo, altrimenti ne crea uno nuovo
        #    markupsNode = slicer.mrmlScene.GetFirstNodeByName(node_name)
        #    if not markupsNode:
        #        markupsNode = slicer.mrmlScene.AddNewNodeByClass(
        #            "vtkMRMLMarkupsFiducialNode", node_name
        #        )
        #        # Personalizza l'aspetto visivo (colore, dimensione)
        #        displayNode = markupsNode.GetDisplayNode()
        #        if displayNode:
        #            displayNode.SetSelectedColor(0.1, 0.8, 0.1)  # Verde
        #            displayNode.SetGlyphScale(2.5)
#
        #    # Pulisci i punti esistenti prima di caricare i nuovi
        #    markupsNode.RemoveAllControlPoints()
#
        #    # Scansiona le ROI e i punti definiti nei moduli del JSON
        #    modules = configData.modules
        #    for module_id, module_info in modules.items():
        #        landmarks = module_info.get("landmarks", [])
#
        #        for lm in landmarks:
        #            name = f"{module_id}_{lm.get('name', 'Punto')}"
        #            # Coordinate [X, Y, Z] relative al fantoccio
        #            coords = lm.get("position", [0.0, 0.0, 0.0])
#
        #            # Aggiunge il punto al nodo di Slicer
        #            markupsNode.AddControlPoint(coords, name)
#
        #    logging.info(
        #        f"Caricati {markupsNode.GetNumberOfControlPoints()} landmark nella scena."
        #)


#
# testTest
#


class CTPhantomQATest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_test1()

    def test_test1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData

        registerSampleData()
        inputVolume = SampleData.downloadSample("test1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = CTPhantomQALogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")
