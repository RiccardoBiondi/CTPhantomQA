import glob
import json
import logging
import os
from pathlib import Path
import sys
from typing import Annotated, Dict

from QACore.config_parser import PhantomConfig
from QACore.roi import ROIManager
from QACore.slicer_renderer import SlicerROIRenderer
import slicer
from slicer import vtkMRMLScalarVolumeNode
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.parameterNodeWrapper import WithinRange, parameterNodeWrapper
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import vtk


#
# test
#


class CTPhantomQA(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:

    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("CTPhantomQA")
        self.parent.categories = ["Radiology"]
        self.parent.dependencies = []
        self.parent.contributors = ["Riccardo Biondi"]

        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """Add data sets to Sample Data module."""
    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        category="test",
        sampleName="test1",
        thumbnailFileName=os.path.join(iconsPath, "test1.png"),
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="test1.nrrd",
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        nodeNames="test1",
    )

    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        category="test",
        sampleName="test2",
        thumbnailFileName=os.path.join(iconsPath, "test2.png"),
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="test2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        nodeNames="test2",
    )


#
# testParameterNode
#


@parameterNodeWrapper
class CTPhantomQAParameterNode:
    """The parameters needed by module."""

    inputVolume: vtkMRMLScalarVolumeNode
    selectedConfigurationFile: Path | str


class CTPhantomQAWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:

    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self) -> None:
        ScriptedLoadableModuleWidget.setup(self)

        uiWidget = slicer.util.loadUI(self.resourcePath("UI/CTPhantomQA.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        uiWidget.setMRMLScene(slicer.mrmlScene)

        self.logic = CTPhantomQALogic()

        # Connections
        self.addObserver(
            slicer.mrmlScene,
            slicer.mrmlScene.StartCloseEvent,
            self.onSceneStartClose,
        )
        self.addObserver(
            slicer.mrmlScene,
            slicer.mrmlScene.EndCloseEvent,
            self.onSceneEndClose,
        )

        # Buttons
        self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)

        # ComboBox Selection Event
        self.ui.jsonSelectorComboBox.connect(
            "currentIndexChanged(int)", self.onJsonSelectionChanged
        )

        # Initializations
        self.initializeParameterNode()
        self.populateJsonComboBox()

    def cleanup(self) -> None:
        self.removeObservers()

    def enter(self) -> None:
        self.initializeParameterNode()
        self.populateJsonComboBox()

    def exit(self) -> None:
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(
                self._parameterNode,
                vtk.vtkCommand.ModifiedEvent,
                self._checkCanApply,
            )

    def onSceneStartClose(self, caller, event) -> None:
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        if self.parent.isEntered:
            self.initializeParameterNode()
            self.populateJsonComboBox()

    def initializeParameterNode(self) -> None:
        self.setParameterNode(self.logic.getParameterNode())

        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass(
                "vtkMRMLScalarVolumeNode"
            )
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode

    def setParameterNode(
        self, inputParameterNode: CTPhantomQAParameterNode | None
    ) -> None:
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(
                self._parameterNode,
                vtk.vtkCommand.ModifiedEvent,
                self._checkCanApply,
            )
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            self._parameterNodeGuiTag = self._parameterNode.connectGui(
                self.ui
            )
            self.addObserver(
                self._parameterNode,
                vtk.vtkCommand.ModifiedEvent,
                self._checkCanApply,
            )
            self._checkCanApply()

    def populateJsonComboBox(self):
        """Scansiona la cartella delle configurazioni JSON e popola la
        QComboBox."""

        # 1. Blocco temporaneo dei segnali per evitare che scattino eventi durante il popolamento
        wasBlocking = self.ui.jsonSelectorComboBox.blockSignals(True)
        self.ui.jsonSelectorComboBox.clear()

        # 2. Definisci il percorso delle configurazioni
        configsDir = os.path.join(
            os.path.dirname(__file__), "Resources/Phantoms"
        )

        if not os.path.exists(configsDir):
            os.makedirs(configsDir)
            logging.warning(f"Created configuration folder: {configsDir}")

        # 3. Aggiungi il Placeholder come prima opzione
        self.ui.jsonSelectorComboBox.addItem(
            "Select Phantom Configuration", None
        )

        # 4. Trova tutti i file .json nella cartella
        jsonFiles = glob.glob(os.path.join(configsDir, "*.json"))

        if not jsonFiles:
            self.ui.jsonSelectorComboBox.blockSignals(wasBlocking)
            self.ui.configurationSummary.setHtml(
                "<i>No JSON configurations found in Resources/Phantoms.</i>"
            )
            return

        # 5. Popola la ComboBox
        for jsonPath in jsonFiles:
            try:
                configData = PhantomConfig.from_json(jsonPath)
                displayName = configData.phantom_name
                self.ui.jsonSelectorComboBox.addItem(displayName, jsonPath)
            except Exception as e:
                logging.error(
                    f"Errore nel caricamento del file JSON {jsonPath}: {e}"
                )

        # 6. Forza la selezione del placeholder (indice 0)
        self.ui.jsonSelectorComboBox.setCurrentIndex(0)

        # 7. Ripristina i segnali senza invocare subito onJsonSelectionChanged
        self.ui.jsonSelectorComboBox.blockSignals(wasBlocking)

        # Testo iniziale riepilogo
        self.ui.configurationSummary.setHtml(
            "<i>Select a configuration from the dropdown to load the phantom.</i>"
        )

    def onJsonSelectionChanged(self):
        """Gestisce l'evento di cambio di selezione del file JSON."""
        comboBox = self.ui.jsonSelectorComboBox
        currentIndex = comboBox.currentIndex

        if currentIndex < 0:
            return

        selectedJsonPath = comboBox.itemData(currentIndex)

        # Se è stato selezionato il placeholder (selectedJsonPath è None)
        if not selectedJsonPath:
            self.ui.configurationSummary.setHtml(
                "<i>No configuration selected.</i>"
            )
            self.logic.renderPhantomROIs(None)
            return

        if os.path.exists(selectedJsonPath):
            if self._parameterNode:
                self._parameterNode.selectedConfigurationFile = Path(
                    selectedJsonPath
                )

            logging.info(f"Selected Configuration: {selectedJsonPath}")
            configData = PhantomConfig.from_json(selectedJsonPath)

            self.updateConfigInfoDisplay(configData)
            self.logic.renderPhantomROIs(configData)

    def updateConfigInfoDisplay(self, configData: PhantomConfig):
        """Costruisce l'HTML di riepilogo per la configurazione selezionata."""
        if not configData:
            self.ui.configurationSummary.setHtml(
                "<i>No configuration selected.</i>"
            )
            return

        html = f"<h3>Phantom Configuration</h3>"
        html += f"<b>Phantom Name:</b> {configData.phantom_name}<br><br>"
        self.ui.configurationSummary.setHtml(html)

    def _checkCanApply(self, caller=None, event=None) -> None:
        pass

    def onApplyButton(self) -> None:
        """Run processing when user clicks "Apply" button."""
        with slicer.util.tryWithErrorDisplay(
            _("Failed to compute results."), waitCursor=True
        ):
            self.logic.process(
                self.ui.inputSelector.currentNode(),
                self.ui.outputSelector.currentNode(),
                self.ui.imageThresholdSliderWidget.value,
                self.ui.invertOutputCheckBox.checked,
            )

            if self.ui.invertedOutputSelector.currentNode():
                self.logic.process(
                    self.ui.inputSelector.currentNode(),
                    self.ui.invertedOutputSelector.currentNode(),
                    self.ui.imageThresholdSliderWidget.value,
                    not self.ui.invertOutputCheckBox.checked,
                    showResult=False,
                )


#
# testLogic
#


class CTPhantomQALogic(ScriptedLoadableModuleLogic):
    """Implementa la logica computazionale del modulo."""

    def __init__(self) -> None:
        ScriptedLoadableModuleLogic.__init__(self)
        self.roi_renderer = SlicerROIRenderer()

    def getParameterNode(self):
        return CTPhantomQAParameterNode(super().getParameterNode())

    def process(
        self, inputVolume: vtkMRMLScalarVolumeNode, selectedConfigurationFile: Path
    ) -> None:
        pass

    def renderPhantomROIs(
        self, configData: PhantomConfig | None
    ) -> Dict[str, "slicer.vtkMRMLMarkupsShapeNode"]:
        """Renderizza tutte le ROI presenti nella configurazione.

        Se configData è None, svuota il manager per rimuovere i nodi esistenti.
        """
        manager = ROIManager()

        if configData:
            for module in configData.modules:
                for roi in module.rois:
                    manager.add_roi(roi)

        # Renderizza (e pulisce gli orfani se manager è vuoto)
        self.roi_renderer.render_all(manager, cleanup_orphans=True)

        # Centra le viste 3D se sono presenti ROI
        if configData:
            slicer.util.resetThreeDViews()
            slicer.util.resetSliceViews()
            logging.info("Rendered ROIs successfully")

        return self.roi_renderer._rendered_nodes


#
# testTest
#


class CTPhantomQATest(ScriptedLoadableModuleTest):
    """Test case per il modulo."""

    def setUp(self):
        slicer.mrmlScene.Clear()

    def runTest(self):
        self.setUp()
        self.test_test1()

    def test_test1(self):
        self.delayDisplay("Starting the test")

        import SampleData

        registerSampleData()
        inputVolume = SampleData.downloadSample("test1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLScalarVolumeNode"
        )
        threshold = 100

        logic = CTPhantomQALogic()

        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")