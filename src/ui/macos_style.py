"""macOS-specific visual styling helpers for PySide6/Qt.

Provides:
  - NSVisualEffectView vibrancy bridging via pyobjc
  - SF Pro font application-wide setup
  - Unified titlebar enabling
  - macOS palette-aware color adaptation
  - Stylesheet generators for pill buttons and rounded cards
"""

import sys
from typing import Optional

if sys.platform != "darwin":
    # No-op on non-macOS platforms
    def apply_macos_styling(window):
        pass

    def set_macos_font(app):
        pass

    def setup_vibrancy(window, material: int = 12):
        pass

    def macos_stylesheet(is_dark: bool = False) -> str:
        return ""

    def apply_macos_palette(app, dark: bool = False):
        pass

    def init_macos_theme(app):
        pass

    def apply_system_theme(app):
        pass

    def button_stylesheet(is_dark: bool = False) -> str:
        return ""

else:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QFontDatabase, QPalette, QColor, QPixmap, QPainter, QIcon
    from PySide6.QtWidgets import QApplication, QWidget, QMainWindow

    def _ns_window(qwindow):
        """Get the NSWindow from a QWindow via pyobjc."""
        try:
            import objc
            from AppKit import NSWindow
            win_id = int(qwindow.winId())
            return objc.pyobjc_id(win_id)
        except Exception:
            return None

    def _ns_view(qwidget: QWidget):
        """Get the NSView from a QWidget."""
        try:
            import objc
            from AppKit import NSView
            win_id = int(qwidget.winId())
            return objc.pyobjc_id(win_id)
        except Exception:
            return None

    def setup_vibrancy(qwindow, material: int = 12):
        """
        Insert an NSVisualEffectView behind the Qt content view.

        material: NSVisualEffectMaterial value.
          12 = NSVisualEffectMaterialSidebar (frosted sidebar look)
           8 = NSVisualEffectMaterialHudWindow
          15 = NSVisualEffectMaterialFullScreenUI
        """
        try:
            from AppKit import (
                NSVisualEffectView,
                NSVisualEffectMaterialSidebar,
                NSVisualEffectStateFollowsWindowActiveState,
            )
            import objc

            ns_view = _ns_view(qwindow)
            if ns_view is None:
                return

            # Create the vibrancy view
            frame = ns_view.frame()
            vev = NSVisualEffectView.alloc().initWithFrame_(frame)
            vev.setMaterial_(NSVisualEffectMaterialSidebar)
            vev.setState_(NSVisualEffectStateFollowsWindowActiveState)
            vev.setBlendingMode_(0)  # NSVisualEffectBlendingModeBehindWindow
            vev.setAutoresizingMask_(18)  # WidthSizable | HeightSizable

            # Insert behind the Qt view
            superview = ns_view.superview()
            if superview:
                superview.addSubview_positioned_relativeTo_(vev, 0, ns_view)
        except Exception:
            pass

    def set_macos_font(app: QApplication, base_size: int = 13):
        """Set SF Pro Text as the default font with Helvetica Neue fallback."""
        families = QFontDatabase.families()
        preferred = None
        for name in ("SF Pro Text", "SF Pro", "SFProText", "Helvetica Neue", "Helvetica"):
            if name in families:
                preferred = name
                break
        if preferred is None:
            return  # System default is fine
        font = QFont(preferred, base_size)
        font.setStyleStrategy(QFont.PreferAntialias)
        app.setFont(font)

    def apply_macos_palette(app: QApplication, dark: bool = False):
        """Apply a macOS-appropriate palette that respects light/dark mode."""
        p = QPalette()
        if dark:
            p.setColor(QPalette.Window, QColor(30, 30, 30, 240))
            p.setColor(QPalette.WindowText, Qt.white)
            p.setColor(QPalette.Base, QColor(40, 40, 40, 220))
            p.setColor(QPalette.AlternateBase, QColor(50, 50, 50, 220))
            p.setColor(QPalette.Text, Qt.white)
            p.setColor(QPalette.Button, QColor(55, 55, 55, 200))
            p.setColor(QPalette.ButtonText, Qt.white)
            p.setColor(QPalette.Highlight, QColor(10, 132, 255))
            p.setColor(QPalette.HighlightedText, Qt.white)
            p.setColor(QPalette.ToolTipBase, QColor(60, 60, 60, 240))
            p.setColor(QPalette.ToolTipText, Qt.white)
        else:
            p.setColor(QPalette.Window, QColor(255, 255, 255, 245))
            p.setColor(QPalette.WindowText, Qt.black)
            p.setColor(QPalette.Base, QColor(255, 255, 255, 230))
            p.setColor(QPalette.AlternateBase, QColor(232, 232, 237, 255))
            p.setColor(QPalette.Text, Qt.black)
            p.setColor(QPalette.Button, QColor(240, 240, 240, 220))
            p.setColor(QPalette.ButtonText, Qt.black)
            p.setColor(QPalette.Highlight, QColor(0, 122, 255))
            p.setColor(QPalette.HighlightedText, Qt.white)
            p.setColor(QPalette.ToolTipBase, QColor(255, 255, 255, 240))
            p.setColor(QPalette.ToolTipText, Qt.black)
        app.setPalette(p)

    def button_stylesheet(is_dark: bool = False) -> str:
        """Return the standard QPushButton stylesheet used across dialogs."""
        if is_dark:
            btn_bg = "rgba(255, 255, 255, 18)"
            btn_hover = "rgba(255, 255, 255, 25)"
            btn_pressed = "rgba(255, 255, 255, 12)"
            text_color = "#FFFFFF"
            disabled_bg = "#48484A"
            disabled_text = "#636366"
        else:
            btn_bg = "rgba(0, 0, 0, 8)"
            btn_hover = "rgba(0, 0, 0, 14)"
            btn_pressed = "rgba(0, 0, 0, 6)"
            text_color = "#1D1D1F"
            disabled_bg = "#C7C7CC"
            disabled_text = "#8E8E93"
        return f"""
            QPushButton {{
                background-color: {btn_bg};
                border: none;
                border-radius: 16px;
                padding: 6px 16px;
                color: {text_color};
                font-weight: 500;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
            QPushButton:pressed {{
                background-color: {btn_pressed};
            }}
            QPushButton:disabled {{
                background-color: {disabled_bg};
                color: {disabled_text};
            }}
            QPushButton:default {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0,122,255,220), stop:1 rgba(0,100,230,220));
                color: white;
            }}
            QPushButton:default:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0,122,255,240), stop:1 rgba(0,100,230,240));
            }}
            QPushButton:default:disabled {{
                background-color: {disabled_bg};
                color: {disabled_text};
            }}
        """

    def macos_stylesheet(is_dark: bool = False) -> str:
        """Generate a stylesheet for pill buttons and rounded cards on macOS."""
        if is_dark:
            btn_bg = "rgba(255, 255, 255, 18)"
            btn_hover = "rgba(255, 255, 255, 25)"
            btn_pressed = "rgba(255, 255, 255, 12)"
            card_bg = "rgba(60, 60, 60, 180)"
            card_border = "rgba(255, 255, 255, 12)"
            table_bg = "rgba(40, 40, 40, 200)"
            table_alt = "rgba(50, 50, 50, 200)"
            header_bg = "rgba(55, 55, 55, 220)"
            text_color = "#FFFFFF"
            sel_bg = "rgba(10, 132, 255, 0.40)"
        else:
            btn_bg = "rgba(0, 0, 0, 8)"
            btn_hover = "rgba(0, 0, 0, 14)"
            btn_pressed = "rgba(0, 0, 0, 6)"
            card_bg = "rgba(250, 250, 250, 220)"
            card_border = "rgba(0, 0, 0, 8)"
            table_bg = "rgba(255, 255, 255, 230)"
            table_alt = "rgba(232, 232, 237, 255)"
            header_bg = "rgba(240, 240, 240, 240)"
            text_color = "#1D1D1F"
            sel_bg = "rgba(0, 122, 255, 0.25)"

        return button_stylesheet(is_dark) + f"""
            /* Rounded cards / containers */
            QFrame#card, QWidget#card {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 12px;
            }}

            /* Table styling */
            QTableWidget {{
                background-color: {table_bg};
                alternate-background-color: {table_alt};
                border: 1px solid {card_border};
                border-radius: 10px;
                gridline-color: {card_border};
                color: {text_color};
            }}
            QTableWidget::item {{
                padding: 4px 8px;
                border-bottom: 1px solid {card_border};
            }}
            QHeaderView::section {{
                background-color: {header_bg};
                color: {text_color};
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid {card_border};
                font-weight: 600;
            }}

            /* List widget styling */
            QListWidget {{
                background-color: {table_bg};
                alternate-background-color: {table_alt};
                border: 1px solid {card_border};
                border-radius: 10px;
                color: {text_color};
                show-decoration-selected: 0;
            }}
            QListWidget::item {{
                padding: 4px 8px;
                border-bottom: 1px solid {card_border};
                background-color: transparent;
                min-height: 28px;
            }}
            QListWidget::item:alternate {{
                background-color: {table_alt};
            }}
            QListWidget::item:!alternate {{
                background-color: {table_bg};
            }}
            QListWidget:!focus {{
                alternate-background-color: {table_alt};
                background-color: {table_bg};
            }}

            /* Scrollbars */
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {btn_bg};
                border-radius: 4px;
                min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {btn_hover};
            }}
            QScrollBar:horizontal {{
                background: transparent;
                height: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: {btn_bg};
                border-radius: 4px;
                min-width: 24px;
            }}

            /* Menu / toolbar cleanup */
            QToolBar {{
                background: transparent;
                border: none;
                spacing: 4px;
                padding: 8px;
                margin-left: 12px;
            }}
            QMenuBar {{
                background: transparent;
                border: none;
            }}
            QMenu {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 8px;
                padding: 6px;
            }}
            QMenu::item {{
                border-radius: 6px;
                padding: 4px 16px;
            }}
            QMenu::item:selected {{
                background-color: {btn_hover};
            }}
        """

    def _is_dark_mode() -> bool:
        """Detect whether macOS is currently in Dark Mode."""
        try:
            from Foundation import NSUserDefaults
            style = NSUserDefaults.standardUserDefaults().stringForKey_("AppleInterfaceStyle")
            return style == "Dark"
        except Exception:
            # Fallback: infer from palette
            app = QApplication.instance()
            if app:
                bg = app.palette().color(QPalette.Window)
                return bg.lightness() < 128
            return False

    def recolor_icon(path: str, color: QColor, size: int = 24) -> QIcon:
        """Load an SVG/image, scale to a uniform *size*, and re-fill all
        opaque pixels with *color*.  Renders at 2× for Retina clarity."""
        from PySide6.QtCore import QSize as _QSize, QFile, QIODevice
        from PySide6.QtSvg import QSvgRenderer

        # Read SVG data via QFile so Qt resource paths (:/...) work
        f = QFile(path)
        if not f.open(QIODevice.ReadOnly):
            return QIcon()
        data = f.readAll()
        f.close()

        renderer = QSvgRenderer(data)
        if not renderer.isValid():
            return QIcon()

        # Render at 2× for Retina displays
        px_size = size * 2
        pixmap = QPixmap(_QSize(px_size, px_size))
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        # Recolor all opaque pixels
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

    def apply_system_theme(app: QApplication):
        """Detect current macOS appearance and apply the matching palette,
        stylesheet, and toolbar icon colors."""
        dark = _is_dark_mode()
        apply_macos_palette(app, dark=dark)
        app.setStyleSheet(macos_stylesheet(is_dark=dark))
        recolor_toolbar_icons(dark)

    def init_macos_theme(app: QApplication):
        """One-time setup: apply font, detect system theme, and connect
        paletteChanged so the app reacts live to dark/light switches.
        Uses the native macOS style (no Fusion override)."""
        set_macos_font(app)
        apply_system_theme(app)
        # Re-apply whenever macOS pushes a new palette (dark ↔ light)
        app.paletteChanged.connect(lambda _palette: apply_system_theme(app))

    def apply_macos_styling(window):
        """
        Apply full macOS styling to a QMainWindow or QDialog.
        Call after setupUi().
        """
        app = QApplication.instance()
        if app is None:
            return

        # 1. Font
        set_macos_font(app)

        # 2. Unified titlebar (main windows only)
        if isinstance(window, QMainWindow):
            window.setUnifiedTitleAndToolBarOnMac(True)

        # 3. Dark mode detection + palette
        dark = _is_dark_mode()
        apply_macos_palette(app, dark=dark)

        # 4. Stylesheet
        app.setStyleSheet(macos_stylesheet(is_dark=dark))

        # 5. Vibrancy (optional, behind Qt content)
        if isinstance(window, QMainWindow):
            cw = window.centralWidget()
            if cw:
                cw.setAttribute(Qt.WA_TranslucentBackground)
                cw.setStyleSheet("background: transparent;")
                window.setAttribute(Qt.WA_TranslucentBackground)
            setup_vibrancy(window, material=12)

        # 6. Native window buttons / full-size content view (main windows only)
        if isinstance(window, QMainWindow):
            try:
                qwin = window.windowHandle()
                if qwin is not None:
                    ns_win = _ns_window(qwin)
                    if ns_win:
                        ns_win.setTitlebarAppearsTransparent_(True)
            except Exception:
                pass
