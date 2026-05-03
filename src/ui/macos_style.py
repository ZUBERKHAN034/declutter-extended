"""macOS-specific visual styling helpers for PySide6/Qt.

Provides:
  - SF Pro font application-wide setup
  - Unified titlebar enabling
  - SVG icon recoloring for light/dark mode
"""

import sys

if sys.platform != "darwin":
    def apply_macos_styling(window):
        pass

    def set_macos_font(app):
        pass

    def init_macos_theme(app):
        pass

    def recolor_icon(path, color, size=24):
        from PySide6.QtGui import QIcon
        return QIcon()

    def recolor_toolbar_icons(dark):
        pass

else:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QFontDatabase, QPalette, QColor, QPixmap, QPainter, QIcon
    from PySide6.QtWidgets import QApplication, QMainWindow

    def set_macos_font(app: QApplication, base_size: int = 13):
        """Set SF Pro Text as the default font with Helvetica Neue fallback."""
        families = QFontDatabase.families()
        preferred = None
        for name in ("SF Pro Text", "SF Pro", "SFProText", "Helvetica Neue", "Helvetica"):
            if name in families:
                preferred = name
                break
        if preferred is None:
            return
        font = QFont(preferred, base_size)
        font.setStyleStrategy(QFont.PreferAntialias)
        app.setFont(font)

    def _is_dark_mode() -> bool:
        """Detect whether macOS is currently in Dark Mode."""
        try:
            from Foundation import NSUserDefaults
            style = NSUserDefaults.standardUserDefaults().stringForKey_("AppleInterfaceStyle")
            return style == "Dark"
        except Exception:
            app = QApplication.instance()
            if app:
                bg = app.palette().color(QPalette.Window)
                return bg.lightness() < 128
            return False

    def recolor_icon(path: str, color: QColor, size: int = 24) -> QIcon:
        """Load an SVG, re-fill opaque pixels with *color*, render at 2×."""
        from PySide6.QtCore import QSize as _QSize, QFile, QIODevice
        from PySide6.QtSvg import QSvgRenderer

        f = QFile(path)
        if not f.open(QIODevice.ReadOnly):
            return QIcon()
        data = f.readAll()
        f.close()

        renderer = QSvgRenderer(data)
        if not renderer.isValid():
            return QIcon()

        px_size = size * 2
        pixmap = QPixmap(_QSize(px_size, px_size))
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), color)
        painter.end()
        pixmap.setDevicePixelRatio(2.0)
        return QIcon(pixmap)

    def recolor_toolbar_icons(dark: bool):
        """Re-tint all QMainWindow toolbar action icons for the active theme."""
        from PySide6.QtGui import QAction as _QAction
        color = QColor(255, 255, 255) if dark else QColor(30, 30, 30)
        app = QApplication.instance()
        if app is None:
            return
        for window in app.topLevelWidgets():
            if not isinstance(window, QMainWindow):
                continue
            for action in window.findChildren(_QAction):
                resource = action.property("_dc_icon_resource")
                if resource:
                    action.setIcon(recolor_icon(resource, color))

    def init_macos_theme(app: QApplication):
        """One-time setup: set font and re-tint toolbar icons on palette changes."""
        set_macos_font(app)
        recolor_toolbar_icons(_is_dark_mode())
        app.paletteChanged.connect(lambda _palette: recolor_toolbar_icons(_is_dark_mode()))

    def apply_macos_styling(window):
        """Apply minimal macOS styling: font + unified titlebar only."""
        app = QApplication.instance()
        if app is None:
            return
        set_macos_font(app)
        if isinstance(window, QMainWindow):
            window.setUnifiedTitleAndToolBarOnMac(True)
