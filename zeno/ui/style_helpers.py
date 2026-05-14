"""All styling logic lives here. Every dialog calls these — no inline stylesheets."""
from PySide6.QtWidgets import QWidget, QPushButton, QLineEdit, QTextEdit, QComboBox, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QCheckBox, QLabel, QTabWidget, QFrame, QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt
from zeno.ui.design_tokens import C, R, is_dark


def style_primary_btn(btn: QPushButton):
    btn.setStyleSheet(f"""
        QPushButton {{ background-color: {C.accent()}; color: #ffffff; border: none; border-radius: {R.button}; padding: 7px 18px; font-family: "SF Pro Text"; font-size: 13px; font-weight: 500; }}
        QPushButton:hover {{ background-color: {C.accent_hover()}; }}
        QPushButton:pressed {{ opacity: 0.8; }}
        QPushButton:disabled {{ background-color: {C.btn_disabled_bg()}; color: {C.btn_disabled_text()}; }}
    """)


def style_secondary_btn(btn: QPushButton):
    btn.setStyleSheet(f"""
        QPushButton {{ background-color: {C.btn_bg()}; color: {C.btn_text()}; border: 1px solid {C.btn_border()}; border-radius: {R.button}; padding: 7px 18px; font-family: "SF Pro Text"; font-size: 13px; }}
        QPushButton:hover {{ background-color: {C.btn_bg_hover()}; }}
        QPushButton:pressed {{ background-color: {C.btn_bg_pressed()}; }}
        QPushButton:disabled {{ background-color: {C.btn_disabled_bg()}; color: {C.btn_disabled_text()}; border-color: transparent; }}
    """)


def style_destructive_btn(btn: QPushButton):
    btn.setStyleSheet(f"""
        QPushButton {{ background-color: transparent; color: {C.error()}; border: 1px solid {C.error()}; border-radius: {R.button}; padding: 7px 18px; font-family: "SF Pro Text"; font-size: 13px; }}
        QPushButton:hover {{ background-color: {C.error()}; color: #ffffff; }}
        QPushButton:disabled {{ color: {C.btn_disabled_text()}; border-color: {C.btn_disabled_bg()}; }}
    """)


def style_line_edit(w: QLineEdit):
    w.setStyleSheet(f"""
        QLineEdit {{ background-color: {C.surface()}; color: {C.text()}; border: 1.5px solid {C.border()}; border-radius: {R.input}; padding: 6px 10px; font-family: "SF Pro Text"; font-size: 13px; }}
        QLineEdit:focus {{ border: 1.5px solid {C.border_focus()}; }}
        QLineEdit:disabled {{ background-color: {C.btn_disabled_bg()}; color: {C.btn_disabled_text()}; }}
    """)


def style_text_edit(w: QTextEdit):
    w.setStyleSheet(f"""
        QTextEdit {{ background-color: {C.surface()}; color: {C.text()}; border: 1.5px solid {C.border()}; border-radius: {R.input}; padding: 8px 10px; font-family: "SF Pro Text"; font-size: 13px; }}
        QTextEdit:focus {{ border: 1.5px solid {C.border_focus()}; }}
    """)


def style_combo_box(w: QComboBox):
    w.setStyleSheet(f"""
        QComboBox {{ background-color: {C.btn_bg()}; color: {C.btn_text()}; border: 1px solid {C.btn_border()}; border-radius: {R.input}; padding: 5px 10px; font-family: "SF Pro Text"; font-size: 13px; min-width: 80px; }}
        QComboBox:hover {{ background-color: {C.btn_bg_hover()}; }}
        QComboBox:disabled {{ background-color: {C.btn_disabled_bg()}; color: {C.btn_disabled_text()}; border-color: transparent; }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
        QComboBox QAbstractItemView {{ background-color: {C.surface()}; color: {C.text()}; border: 1px solid {C.border()}; border-radius: {R.card}; selection-background-color: {C.row_selected()}; selection-color: {C.row_selected_text()}; padding: 4px; margin: 2px; outline: none; }}
        QComboBox QAbstractItemView::item {{ padding: 6px 10px; border-radius: {R.inner}; }}
        QComboBox QAbstractItemView::item:hover {{ background-color: {C.accent()}; color: #ffffff; }}
        QComboBox QAbstractItemView::item:selected {{ background-color: {C.accent()}; color: #ffffff; }}
    """)

    # Remove inner square frame from the view; keep native macOS popup rounding
    w.view().setFrameShape(QFrame.Shape.NoFrame)
    w.view().setFrameShadow(QFrame.Shadow.Plain)
    w.view().setLineWidth(0)


def style_list_widget(w: QListWidget):
    # Remove native frame so macOS doesn't draw a square border on top
    w.setFrameShape(QFrame.Shape.NoFrame)
    # Force Qt to honour the stylesheet for background painting
    w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    # Make the viewport transparent so the rounded outer border isn't
    # covered by a rectangular viewport fill
    w.viewport().setAutoFillBackground(False)
    w.setAlternatingRowColors(True)
    w.setStyleSheet(f"""
        QListWidget {{ background-color: {C.row_bg()}; alternate-background-color: {C.row_alt()}; color: {C.text()}; border: 1.5px solid {C.border()}; border-radius: {R.card}; outline: none; padding: 3px; font-family: "SF Pro Text"; font-size: 13px; }}
        QListWidget::item {{ padding: 7px 10px; border-radius: {R.inner}; color: {C.text()}; }}
        QListWidget::item:hover:!selected {{ background-color: {C.row_hover()}; }}
        QListWidget::item:selected {{ background-color: {C.row_selected()}; color: {C.row_selected_text()}; }}
        QListWidget::item:selected:!active {{ background-color: {C.row_selected()}; color: {C.row_selected_text()}; }}
    """)
    p = w.palette()
    p.setColor(QPalette.ColorRole.Base, QColor(C.row_bg()))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(C.row_alt()))
    p.setColor(QPalette.ColorRole.Text, QColor(C.text()))
    p.setColor(QPalette.ColorRole.Highlight, QColor(C.row_selected()))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(C.row_selected_text()))
    w.setPalette(p)


def _visible_row_capacity(list_widget: QListWidget) -> int:
    """Return how many rows fit in the current viewport without scrolling."""
    viewport = list_widget.viewport()
    if not viewport:
        return 6
    h = viewport.height()
    rh = list_widget.sizeHintForRow(0)
    if rh <= 0:
        rh = 30
    return max(6, h // rh)


def populate_styled_list(list_widget: QListWidget, items, fill_empty_rows: bool = True):
    """Populate a QListWidget, relying on style_list_widget's alternating palette."""
    list_widget.clear()
    list_widget.reset()
    all_items = list(items) if items else []

    if not all_items:
        start = 0
    else:
        for text in all_items:
            item = QListWidgetItem(text)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            list_widget.addItem(item)
        start = len(all_items)

    # Pad with empty rows to fill the visible area (no scrolling until real items overflow)
    cap = _visible_row_capacity(list_widget)
    DEFAULT_PAD = 5  # small padding for subtle two-tone effect
    pad = DEFAULT_PAD if fill_empty_rows else max(0, cap - start)
    for _ in range(start, start + pad):
        empty = QListWidgetItem("")
        empty.setFlags(Qt.NoItemFlags)
        list_widget.addItem(empty)


def populate_styled_table(table_widget: QTableWidget, row_count: int, fill_empty_rows: bool = True):
    """Set row count for a QTableWidget and pad with empty rows for two-tone effect."""
    if row_count == 0:
        table_widget.setRowCount(0)
        return

    if fill_empty_rows:
        # Calculate how many rows are visible
        viewport = table_widget.viewport()
        if viewport:
            QApplication.processEvents()
            viewport_height = viewport.height()
            row_height = table_widget.rowHeight(0)
            if row_height <= 0:
                row_height = 30
            visible_rows = max(1, viewport_height // row_height)
        else:
            visible_rows = 6

        # Add padding to fill visible area if needed
        total_rows = max(row_count, visible_rows)
        table_widget.setRowCount(total_rows)

        # Add empty cells for padding rows
        for i in range(row_count, total_rows):
            for col in range(table_widget.columnCount()):
                item = table_widget.item(i, col)
                if item is None:
                    empty = QTableWidgetItem("")
                    empty.setFlags(Qt.NoItemFlags)
                    table_widget.setItem(i, col, empty)
    else:
        table_widget.setRowCount(row_count)


def _recalculate_table_padding(table_widget: QTableWidget):
    """Recalculate padding rows for a table widget after resize."""
    from zeno.ui.widgets import MacTableWidget

    # Get actual row count from data (count non-empty rows)
    actual_count = 0
    for i in range(table_widget.rowCount()):
        has_data = False
        for col in range(table_widget.columnCount()):
            item = table_widget.item(i, col)
            if item and item.flags() & Qt.ItemIsEnabled:
                has_data = True
                break
        if has_data:
            actual_count = i + 1

    if actual_count == 0:
        return

    if isinstance(table_widget, MacTableWidget):
        table_widget.setActualRowCount(actual_count)

    # Get visible row capacity
    viewport = table_widget.viewport()
    if not viewport:
        return

    QApplication.processEvents()
    viewport_height = viewport.height()
    row_height = table_widget.rowHeight(0)
    if row_height <= 0:
        row_height = 30

    visible_rows = max(1, viewport_height // row_height)
    total_rows = max(actual_count, visible_rows)

    if table_widget.rowCount() != total_rows:
        table_widget.setRowCount(total_rows)

        # Add empty cells for padding if needed
        for i in range(actual_count, total_rows):
            for col in range(table_widget.columnCount()):
                if table_widget.item(i, col) is None:
                    empty = QTableWidgetItem("")
                    empty.setFlags(Qt.NoItemFlags)
                    table_widget.setItem(i, col, empty)


def _clear_table_padding(table_widget: QTableWidget):
    """Clear padding rows when user scrolls."""
    from zeno.ui.widgets import MacTableWidget

    # Count actual rows with data
    actual_count = 0
    for i in range(table_widget.rowCount()):
        has_data = False
        for col in range(table_widget.columnCount()):
            item = table_widget.item(i, col)
            if item and item.flags() & Qt.ItemIsEnabled:
                has_data = True
                break
        if has_data:
            actual_count = i + 1

    if isinstance(table_widget, MacTableWidget):
        table_widget.setActualRowCount(actual_count)

    if actual_count > 0 and table_widget.rowCount() > actual_count:
        table_widget.setRowCount(actual_count)


def style_table_widget(w: QTableWidget):
    w.setAlternatingRowColors(True)
    w.setShowGrid(False)
    # Remove native frame so macOS doesn't draw a square border on top
    w.setFrameShape(QFrame.Shape.NoFrame)
    # Force Qt to honour the stylesheet for background painting
    w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    # Make the viewport transparent so the rounded outer border isn't covered
    w.viewport().setAutoFillBackground(False)
    
    w.horizontalHeader().setHighlightSections(False)
    w.verticalHeader().setVisible(False)
    w.setStyleSheet(f"""
        QTableWidget {{ background-color: {C.row_bg()}; alternate-background-color: {C.row_alt()}; color: {C.text()}; border: 1.5px solid {C.border()}; border-radius: {R.card}; outline: none; font-family: "SF Pro Text"; font-size: 13px; }}
        QTableWidget::item {{ padding: 7px 12px; }}
        QTableWidget::item:hover:!selected {{ background-color: {C.row_hover()}; }}
        QTableWidget::item:selected {{ background-color: {C.row_selected()}; color: {C.row_selected_text()}; }}
        QTableWidget::item:selected:!active {{ background-color: {C.row_selected()}; color: {C.row_selected_text()}; }}
        QHeaderView {{ background-color: {C.surface_alt()}; border-top-left-radius: {R.card}; border-top-right-radius: {R.card}; }}
        QHeaderView::section {{ background-color: transparent; color: {C.text_secondary()}; border: none; border-bottom: 1px solid {C.border()}; padding: 6px 12px; font-family: "SF Pro Text"; font-size: 11px; font-weight: 600; }}
    """)
    p = w.palette()
    p.setColor(QPalette.ColorRole.Base, QColor(C.row_bg()))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(C.row_alt()))
    p.setColor(QPalette.ColorRole.Text, QColor(C.text()))
    p.setColor(QPalette.ColorRole.Highlight, QColor(C.row_selected()))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(C.row_selected_text()))
    w.setPalette(p)


def style_checkbox(w: QCheckBox):
    # Absolute path to the white checkmark SVG (Qt QSS needs a real file)
    import os
    _tick = os.path.join(
        os.path.dirname(__file__), "..", "..", "assets", "check_white.svg"
    ).replace("\\", "/")
    w.setStyleSheet(f"""
        QCheckBox {{ color: {C.text()}; font-family: "SF Pro Text"; font-size: 13px; spacing: 6px; }}
        QCheckBox::indicator {{ width: 16px; height: 16px; border: 1.5px solid {C.border()}; border-radius: 4px; background-color: {C.surface()}; }}
        QCheckBox::indicator:checked {{ background-color: {C.accent()}; border-color: {C.accent()}; image: url("{_tick}"); }}
        QCheckBox::indicator:hover {{ border-color: {C.border_focus()}; }}
    """)


def style_radio_button(w):
    w.setStyleSheet(f"""
        QRadioButton {{ color: {C.text()}; font-family: "SF Pro Text"; font-size: 13px; spacing: 6px; }}
        QRadioButton::indicator {{ width: 14px; height: 14px; border: 1.5px solid {C.border()}; border-radius: 7px; background-color: {C.surface()}; }}
        QRadioButton::indicator:checked {{ background-color: {C.accent()}; border-color: {C.accent()}; }}
        QRadioButton::indicator:hover {{ border-color: {C.border_focus()}; }}
    """)


def style_section_label(lbl: QLabel):
    lbl.setStyleSheet(f"""
        QLabel {{ color: {C.text()}; font-family: "SF Pro Text"; font-size: 13px; font-weight: 600; background: transparent; }}
    """)


def style_status_label(lbl: QWidget, status: str = "normal"):
    color = {"success": C.success(), "error": C.error(), "warning": C.warning(), "normal": C.text_secondary()}.get(status, C.text_secondary())
    bg = {"error": "#fff5f5" if not is_dark() else "#2d1a1a", "success": "#f5fff9" if not is_dark() else "#1a2d21"}.get(status, "transparent")
    border = {"error": C.error(), "success": C.success()}.get(status, "transparent")
    
    selector = "QLabel, QTextEdit"
    lbl.setStyleSheet(f"""
        {selector} {{ 
            color: {color}; 
            font-family: "SF Pro Text"; 
            font-size: 13px; 
            padding: 8px 12px;
            background-color: {bg};
            border: 1px solid {border};
            border-radius: {R.inner};
        }}
    """)


def style_loading_btn(btn):
    # This styling is dynamic because it depends on the internal state (success/error/retry)
    base_bg = C.accent()
    is_loading = getattr(btn, "_is_loading", False)
    state = getattr(btn, "_state", "normal")
    
    if state == "success":
        base_bg = C.success()
    elif state == "error" or state == "retry":
        base_bg = C.error()
            
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {base_bg};
            color: #ffffff;
            border-radius: {R.button};
            padding: 7px 18px;
            font-family: "SF Pro Text";
            font-size: 13px;
            font-weight: 600;
            border: none;
        }}
        QPushButton:hover {{ 
            background-color: {base_bg if btn.isEnabled() else C.btn_disabled_bg()};
            opacity: 0.9;
        }}
        QPushButton:disabled {{ 
            background-color: {C.btn_disabled_bg() if not is_loading and state != "retry" else base_bg}; 
            color: {C.btn_disabled_text() if not is_loading and state != "retry" else "#ffffff"}; 
        }}
    """)


def style_tab_widget(w: QTabWidget):
    w.setStyleSheet(f"""
        QTabWidget::pane {{ border: 1px solid {C.border()}; border-radius: {R.card}; background-color: {C.surface()}; top: -1px; }}
        QTabWidget::tab-bar {{ alignment: center; }}
        QTabBar::tab {{ background: transparent; color: {C.text_secondary()}; padding: 7px 16px; border: none; font-family: "SF Pro Text"; font-size: 13px; }}
        QTabBar::tab:selected {{ color: {C.text()}; font-weight: 600; border-bottom: 2px solid {C.accent()}; }}
        QTabBar::tab:hover:!selected {{ color: {C.text()}; }}
    """)


def style_dialog(dlg: QWidget):
    dlg.setStyleSheet(f"""
        QDialog, QWidget#centralWidget {{ background-color: {C.bg()}; color: {C.text()}; font-family: "SF Pro Text"; font-size: 13px; }}
    """)


def style_group_box(w):
    w.setStyleSheet(f"""
        QGroupBox {{ color: {C.text()}; font-family: "SF Pro Text"; font-size: 13px; font-weight: 600; border: 1px solid {C.border()}; border-radius: {R.card}; margin-top: 12px; padding-top: 12px; padding: 12px; background: transparent; }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 8px; top: -2px; padding: 0 4px; background: {C.bg()}; }}
    """)


def style_toolbar(tb):
    tb.setStyleSheet(f"""
        QToolBar {{ background: transparent; border: none; spacing: 4px; padding: 8px; }}
    """)


def style_separator(w):
    w.setStyleSheet(f"""
        QFrame {{
            border: none;
            border-top: 1px solid {C.border()};
            margin: 6px 0px;
        }}
    """)


def reapply_styles(root: QWidget, apply_fn):
    """Call apply_fn then force update on all children."""
    apply_fn()
    for w in root.findChildren(QWidget):
        w.update()
    root.update()


def styled_confirm_dialog(
    parent,
    title: str,
    message: str,
    confirm_text: str = "Yes",
    cancel_text: str = "Cancel",
    destructive: bool = False,
    icon_resource: str = ":/images/icons/question-circle.svg",
) -> bool:
    """Show a styled confirmation dialog that matches the design system.

    Returns True if the user confirmed, False otherwise.
    """
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
    from PySide6.QtCore import Qt, QSize
    from PySide6.QtGui import QPixmap, QPainter, QColor as _QColor
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtCore import QFile, QIODevice

    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setFixedWidth(380)
    dlg.setModal(True)

    # --- Load and recolor icon ------------------------------------------------
    icon_color = _QColor(C.text())
    f = QFile(icon_resource)
    icon_pixmap = None
    if f.open(QIODevice.ReadOnly):
        data = f.readAll()
        f.close()
        renderer = QSvgRenderer(data)
        if renderer.isValid():
            px_size = 96
            icon_pixmap = QPixmap(QSize(px_size, px_size))
            icon_pixmap.fill(Qt.transparent)
            painter = QPainter(icon_pixmap)
            renderer.render(painter)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(icon_pixmap.rect(), icon_color)
            painter.end()
            icon_pixmap.setDevicePixelRatio(2.0)

    # --- Layout ---------------------------------------------------------------
    layout = QVBoxLayout(dlg)
    layout.setSpacing(16)
    layout.setContentsMargins(28, 28, 28, 24)

    if icon_pixmap:
        icon_label = QLabel()
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedHeight(52)
        layout.addWidget(icon_label)

    title_label = QLabel(title)
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setWordWrap(True)
    title_label.setStyleSheet(f"""
        QLabel {{ color: {C.text()}; font-family: "SF Pro Text"; font-size: 15px; font-weight: 600; background: transparent; }}
    """)
    layout.addWidget(title_label)

    msg_label = QLabel(message)
    msg_label.setAlignment(Qt.AlignCenter)
    msg_label.setWordWrap(True)
    msg_label.setStyleSheet(f"""
        QLabel {{ color: {C.text_secondary()}; font-family: "SF Pro Text"; font-size: 13px; background: transparent; }}
    """)
    layout.addWidget(msg_label)

    layout.addSpacing(4)

    # --- Buttons --------------------------------------------------------------
    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(12)

    cancel_btn = QPushButton(cancel_text)
    style_secondary_btn(cancel_btn)
    cancel_btn.setMinimumHeight(34)
    cancel_btn.setCursor(Qt.PointingHandCursor)
    cancel_btn.clicked.connect(dlg.reject)
    btn_layout.addWidget(cancel_btn)

    confirm_btn = QPushButton(confirm_text)
    confirm_btn.setMinimumHeight(34)
    confirm_btn.setCursor(Qt.PointingHandCursor)
    if destructive:
        style_destructive_btn(confirm_btn)
    else:
        style_primary_btn(confirm_btn)
    confirm_btn.clicked.connect(dlg.accept)
    confirm_btn.setDefault(True)
    btn_layout.addWidget(confirm_btn)

    layout.addLayout(btn_layout)

    # --- Dialog styling -------------------------------------------------------
    dlg.setStyleSheet(f"""
        QDialog {{
            background-color: {C.bg()};
            border-radius: {R.card};
        }}
    """)

    return dlg.exec() == QDialog.DialogCode.Accepted

