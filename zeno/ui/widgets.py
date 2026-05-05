"""Custom widget subclasses for macOS-native appearance."""

from PySide6.QtWidgets import QComboBox, QListView, QFrame, QTableWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor


class MacComboBox(QComboBox):
    """QComboBox subclass that removes the native macOS popup container square.

    On macOS the popup dropdown sits inside a QComboBoxPrivateContainer
    (a QFrame subclass) that draws an opaque square background behind the
    styled QAbstractItemView, creating a visible rectangular artifact
    behind rounded corners.

    This subclass makes the container transparent using widget attributes
    and palette (NOT stylesheets, which would cascade to child widgets
    and make the actual list items invisible too).
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Replace default view with a clean QListView
        view = QListView(self)
        view.setFrameShape(QFrame.Shape.NoFrame)
        view.setFrameShadow(QFrame.Shadow.Plain)
        view.setLineWidth(0)
        view.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setView(view)

    def showPopup(self):
        super().showPopup()

        # The popup container is view().parentWidget() — an internal
        # QComboBoxPrivateContainer (QFrame subclass).  It draws the
        # opaque square background behind the rounded QListView.
        #
        # We make only THIS widget transparent using attributes and
        # palette — NOT setStyleSheet, which would cascade down to the
        # QListView and make the item backgrounds invisible.
        container = self.view().parentWidget()
        if container:
            # Remove the QFrame border/shadow
            if isinstance(container, QFrame):
                container.setFrameShape(QFrame.Shape.NoFrame)
                container.setFrameShadow(QFrame.Shadow.Plain)
                container.setLineWidth(0)

            # Make the container's own background transparent
            container.setAttribute(
                Qt.WidgetAttribute.WA_TranslucentBackground, True
            )
            container.setAutoFillBackground(False)

            # Clear the container's palette background to fully transparent
            pal = container.palette()
            pal.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 0))
            pal.setColor(QPalette.ColorRole.Base, QColor(0, 0, 0, 0))
            container.setPalette(pal)

        # Also fix the popup window itself (removes macOS drop shadow)
        popup_window = self.view().window()
        if popup_window and popup_window is not self.window():
            popup_window.setWindowFlags(
                Qt.WindowType.Popup
                | Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.NoDropShadowWindowHint
            )
            popup_window.setAttribute(
                Qt.WidgetAttribute.WA_TranslucentBackground, True
            )
            popup_window.show()


class MacTableWidget(QTableWidget):
    """QTableWidget subclass that extends alternating row colors to the bottom.

    By default, QTableWidget only paints alternating row colors for rows
    that actually contain data. This subclass intercepts the viewport's
    paint event to draw the alternating pattern over the empty space
    all the way to the bottom of the table.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, event):
        # Let the table paint its items and grid first
        super().paintEvent(event)

        if self.alternatingRowColors():
            from PySide6.QtGui import QPainter, QPainterPath
            from PySide6.QtCore import QRect, QRectF
            
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Clip the alternating rows to the table's border radius (inner radius ~8.5)
            # This prevents the custom row painter from drawing square corners
            # at the bottom of the rounded QTableWidget.
            path = QPainterPath()
            path.addRoundedRect(QRectF(self.viewport().rect()), 8.5, 8.5)
            painter.setClipPath(path)
            
            painter.setPen(Qt.PenStyle.NoPen)
            
            row_height = self.verticalHeader().defaultSectionSize()
            if row_height <= 0:
                row_height = 30
            
            # Find the Y position where the last row ends
            last_row = self.rowCount() - 1
            if last_row >= 0:
                y = self.rowViewportPosition(last_row) + self.rowHeight(last_row)
            else:
                y = 0
            
            viewport_height = self.viewport().height()
            viewport_width = self.viewport().width()
            alt_color = self.palette().color(QPalette.ColorRole.AlternateBase)
            
            # Start drawing alternating rectangles down the empty space
            current_row = self.rowCount()
            while y < viewport_height:
                if current_row % 2 != 0:
                    painter.fillRect(QRect(0, y, viewport_width, row_height), alt_color)
                y += row_height
                current_row += 1
                
            painter.end()
