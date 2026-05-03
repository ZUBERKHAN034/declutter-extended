"""Single source of truth for all color values. No hex anywhere else."""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette


def is_dark() -> bool:
    app = QApplication.instance()
    if app is None:
        return False
    return app.palette().color(QPalette.ColorRole.Window).lightness() < 128


class C:
    @staticmethod
    def bg() -> str:
        return "#1c1c1e" if is_dark() else "#f5f5f7"

    @staticmethod
    def surface() -> str:
        return "#2c2c2e" if is_dark() else "#ffffff"

    @staticmethod
    def surface_alt() -> str:
        return "#3a3a3c" if is_dark() else "#f2f2f7"

    @staticmethod
    def border() -> str:
        return "#3a3a3c" if is_dark() else "#d1d1d6"

    @staticmethod
    def border_focus() -> str:
        return "#0a84ff" if is_dark() else "#007aff"

    @staticmethod
    def text() -> str:
        return "#ffffff" if is_dark() else "#000000"

    @staticmethod
    def text_secondary() -> str:
        return "#8e8e93" if is_dark() else "#6c6c70"

    @staticmethod
    def accent() -> str:
        return "#0a84ff" if is_dark() else "#007aff"

    @staticmethod
    def accent_hover() -> str:
        return "#409cff" if is_dark() else "#0066dd"

    @staticmethod
    def btn_bg() -> str:
        return "#3a3a3c" if is_dark() else "#ffffff"

    @staticmethod
    def btn_bg_hover() -> str:
        return "#48484a" if is_dark() else "#f2f2f7"

    @staticmethod
    def btn_bg_pressed() -> str:
        return "#636366" if is_dark() else "#e5e5ea"

    @staticmethod
    def btn_border() -> str:
        return "#636366" if is_dark() else "#c7c7cc"

    @staticmethod
    def btn_text() -> str:
        return "#ffffff" if is_dark() else "#000000"

    @staticmethod
    def btn_disabled_bg() -> str:
        return "#2c2c2e" if is_dark() else "#f2f2f7"

    @staticmethod
    def btn_disabled_text() -> str:
        return "#636366" if is_dark() else "#c7c7cc"

    @staticmethod
    def row_bg() -> str:
        return "#2c2c2e" if is_dark() else "#ffffff"

    @staticmethod
    def row_alt() -> str:
        return "#3a3a3c" if is_dark() else "#f9f9fb"

    @staticmethod
    def row_hover() -> str:
        return "#48484a" if is_dark() else "#e5e5ea"

    @staticmethod
    def row_selected() -> str:
        return "#0a84ff" if is_dark() else "#007aff"

    @staticmethod
    def row_selected_text() -> str:
        return "#ffffff"

    @staticmethod
    def success() -> str:
        return "#30d158" if is_dark() else "#34c759"

    @staticmethod
    def error() -> str:
        return "#ff453a" if is_dark() else "#ff3b30"

    @staticmethod
    def warning() -> str:
        return "#ffd60a" if is_dark() else "#ffcc00"


class R:
    button = "8px"
    input = "7px"
    card = "10px"
    inner = "5px"
