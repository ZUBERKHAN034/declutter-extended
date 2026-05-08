"""Advanced button with loading spinner and state-based feedback (Success/Error/Retry)."""

from PySide6.QtWidgets import QPushButton, QComboBox, QListView, QFrame, QTableWidget, QStyle, QStyleOptionButton
from PySide6.QtCore import Qt, QTimer, QRectF, QRect, Signal as _Signal
from PySide6.QtGui import QPainter, QColor, QPen, QPalette

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
    """Custom QTableWidget with macOS-native styling."""
    def __init__(self, parent=None):
        super().__init__(parent)

class LoadingButton(QPushButton):
    """
    A button that shows a spinner when busy and can display success/error states.
    Now includes a retry countdown.
    """
    retry_ready = _Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._is_loading = False
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.setInterval(30) # ~33 FPS
        
        self._state = "normal" # normal, success, error, retry
        self._original_text = text
        self._state_timer = QTimer(self)
        self._state_timer.setSingleShot(True)
        self._state_timer.timeout.connect(self.reset_state)

        # Pulsing animation for loading state
        self._pulse_alpha = 255
        self._pulse_dir = -8
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._update_pulse)
        self._pulse_timer.setInterval(40)

        # Retry timer logic
        self._retry_countdown = 0
        self._retry_timer = QTimer(self)
        self._retry_timer.timeout.connect(self._update_retry_countdown)
        self._retry_timer.setInterval(1000)

    def start_loading(self, loading_text=None):
        self._stop_all_timers()
        self._is_loading = True
        self._state = "normal"
        if loading_text:
            self.setText(loading_text)
        self.setEnabled(False)
        self._timer.start()
        self._pulse_timer.start()
        self.update_style()
        self.update()

    def stop_loading(self, original_text=None):
        self._is_loading = False
        self._timer.stop()
        self._pulse_timer.stop()
        if original_text:
            self._original_text = original_text
        self.setText(self._original_text)
        self.setEnabled(True)
        self.update_style()
        self.update()

    def show_success(self, message="Success", duration=2000):
        self.stop_loading()
        self._state = "success"
        self.setText(message)
        self._state_timer.start(duration)
        self.update_style()
        self.update()

    def show_error(self, message="Error", duration=3000):
        self.stop_loading()
        self._state = "error"
        self.setText(message)
        self._state_timer.start(duration)
        self.update_style()
        self.update()

    def show_retry(self, seconds=5):
        self.stop_loading()
        self._state = "retry"
        self._retry_countdown = seconds
        self.setEnabled(False)
        self.setText(f"Retry in {self._retry_countdown}s")
        self._retry_timer.start()
        self.update_style()
        self.update()

    def _update_retry_countdown(self):
        self._retry_countdown -= 1
        if self._retry_countdown <= 0:
            self._retry_timer.stop()
            self.reset_state()
            self.setEnabled(True)
            self.retry_ready.emit()
        else:
            self.setText(f"Retry in {self._retry_countdown}s")
            self.update()

    def reset_state(self):
        self._stop_all_timers()
        self._state = "normal"
        self.setText(self._original_text)
        self.setEnabled(True)
        self.update_style()
        self.update()

    def _stop_all_timers(self):
        self._timer.stop()
        self._pulse_timer.stop()
        self._retry_timer.stop()
        self._state_timer.stop()
        self._is_loading = False

    def update_style(self):
        try:
            from zeno.ui.style_helpers import style_loading_btn
            style_loading_btn(self)
        except ImportError:
            pass

    def _rotate(self):
        self._angle = (self._angle + 30) % 360
        self.update()

    def _update_pulse(self):
        self._pulse_alpha += self._pulse_dir
        if self._pulse_alpha <= 160 or self._pulse_alpha >= 255:
            self._pulse_dir *= -1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        
        actual_text = opt.text
        is_busy = self._is_loading or self._state != "normal"
        
        # Don't let the style draw the text if we're busy
        if is_busy:
            opt.text = ""
            
        # Draw the button background and border
        self.style().drawControl(QStyle.ControlElement.CE_PushButton, opt, painter, self)
        
        if is_busy:
            rect = self.rect()
            metrics = self.fontMetrics()
            text_width = metrics.horizontalAdvance(actual_text)
            
            # Text color (always white for accent/success/error backgrounds)
            text_color = QColor("#ffffff")
            if self._is_loading:
                # Apply pulse to text too
                text_color.setAlpha(self._pulse_alpha)
                
            painter.setPen(text_color)
            font = self.font()
            if self._state != "normal":
                font.setBold(True)
            painter.setFont(font)
            
            if self._is_loading:
                size = 14
                gap = 10
                total_width = size + gap + text_width
                start_x = (rect.width() - total_width) / 2
                
                # Draw spinner
                spinner_rect = QRectF(start_x, (rect.height() - size) / 2, size, size)
                painter.save()
                painter.translate(spinner_rect.center())
                painter.rotate(self._angle)
                painter.translate(-spinner_rect.center())
                
                pen = QPen(text_color)
                pen.setWidth(2)
                pen.setCapStyle(Qt.RoundCap)
                painter.setPen(pen)
                painter.drawArc(spinner_rect, 0, 270 * 16)
                painter.restore()
                
                # Draw text
                text_rect = QRect(start_x + size + gap, 0, text_width, rect.height())
            else:
                # Centered text for Success/Error/Retry
                text_rect = QRect(0, 0, rect.width(), rect.height())
                
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, actual_text)
