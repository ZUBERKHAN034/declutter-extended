from cx_Freeze import setup, Executable
import os
from zeno.config import VERSION as APP_VERSION

build_exe_options = {
    "excludes": [
        "tkinter", "pandas", "matplotlib", "scipy", "numpy",
        # PySide6-specific exclusions for unused Qt modules
        "PySide6.Qt3DAnimation", "PySide6.Qt3DCore", "PySide6.Qt3DExtras",
        "PySide6.Qt3DInput", "PySide6.Qt3DLogic", "PySide6.Qt3DRender",
        "PySide6.QtBluetooth", "PySide6.QtCharts", "PySide6.QtDataVisualization",
        "PySide6.QtGamepad", "PySide6.QtNetworkAuth", "PySide6.QtNfc", "PySide6.QtOpenGL",
        "PySide6.QtPdf", "PySide6.QtPdfWidgets", "PySide6.QtPositioning",
        "PySide6.QtPrintSupport", "PySide6.QtQuick3D", "PySide6.QtQuickControls2",
        "PySide6.QtQuickParticles", "PySide6.QtQuickShapes", "PySide6.QtQuickWidgets",
        "PySide6.QtRemoteObjects", "PySide6.QtScript", "PySide6.QtScriptTools",
        "PySide6.QtSensors", "PySide6.QtSerialBus", "PySide6.QtSerialPort",
        "PySide6.QtSql", "PySide6.QtSvg", "PySide6.QtTextToSpeech",
        "PySide6.QtVirtualKeyboard", "PySide6.QtWebChannel", "PySide6.QtWebEngine",
        "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebSockets", "PySide6.QtXmlPatterns"
    ],
    "packages": ["os", "sys", "collections", "PySide6", "zeno", "requests", "certifi", "charset_normalizer"],
    "include_files": [
        os.path.join("assets", "zeno_logo.icns"),
    ],
    "optimize": 2
}

setup(
    name="Zeno",
    version=APP_VERSION,
    description="Zeno: file organizer",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            os.path.join("src", "Zeno.py"),
            icon=os.path.join("assets", "zeno_logo.icns")
        )
    ]
)
