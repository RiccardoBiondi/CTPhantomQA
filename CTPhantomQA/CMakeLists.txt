# ... (Codice generato automaticamente da Slicer in alto) ...

set(MODULE_PYTHON_SCRIPTS
  CTPhantomQA.py
  )

# 1. DICHIARA I TUOI SCRIPT PYTHON PERSONALIZZATI
set(MODULE_PYTHON_RESOURCES
  QACore/__init__.py
  QACore/config_parser.py
  QACore/evaluators.py
  QACore/pdf_exporter.py
  )

# 2. DICHIARA I TUOI FILE JSON DI CONFIGURAZIONE
set(MODULE_DATA_FILES
  Resources/Phantoms/catphan600.json
  Resources/Phantoms/catphan504.json
  )

# ... (Cerca la sezione SlicerMacroBuildScriptedModule nel file) ...

SlicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  SOURCES ${MODULE_PYTHON_RESOURCES} # <-- Assicurati che Slicer veda QACore
  DATA_FILES ${MODULE_DATA_FILES}    # <-- Assicurati che Slicer veda i JSON
  WITH_RUN_TEST
  )
