from PySide6.QtWidgets import (
    QDialog, QTableWidgetItem, QApplication, QMessageBox,
    QLineEdit, QComboBox, QRadioButton, QDialogButtonBox, QHBoxLayout, QVBoxLayout, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QThread, QTimer, Signal as _Signal
from zeno.config import VERSION
from zeno.store import load_settings, save_settings
from src.startup import is_enabled as startup_is_enabled, enable as startup_enable, disable as startup_disable

from src.ui.ui_settings_dialog import Ui_settingsDialog
from src.ui.macos_style import apply_macos_styling
from zeno.ui.design_tokens import C
from zeno.ui.style_helpers import (
    style_dialog,
    style_tab_widget,
    style_table_widget,
    style_group_box,
    style_line_edit,
    style_combo_box,
    style_checkbox,
    style_radio_button,
    style_primary_btn,
    style_secondary_btn,
    style_loading_btn,
    style_status_label,
    reapply_styles,
)
from zeno.ui.widgets import LoadingButton

import sys

if sys.platform == "darwin":
    from zeno.ai.gemini_service import GeminiService, MODEL_CHOICES


class _GeminiTestWorker(QThread):
    """Background thread that verifies a Gemini API key."""

    success = _Signal()
    failure = _Signal(str)

    def __init__(self, api_key: str, model: str, parent=None):
        super().__init__(parent)
        self._api_key = api_key
        self._model = model

    def run(self):
        try:
            svc = GeminiService(self._api_key, model=self._model)
            # Minimal harmless prompt to verify connectivity
            svc._client.models.generate_content(
                model=svc._model,
                contents="Hello",
            )
            self.success.emit()
        except Exception as exc:
            msg = GeminiService.map_gemini_error(exc)
            self.failure.emit(msg)


class SettingsDialog(QDialog):
    def __init__(self):
        super(SettingsDialog, self).__init__()
        self.ui = Ui_settingsDialog()
        self.ui.setupUi(self)
        self.setMinimumSize(560, 520)
        self.resize(560, 520)
        self.ui.aboutVersionLabel.setText(f"Version {VERSION}")
        from PySide6.QtGui import QPixmap
        import os, sys
        try:
            _base = sys._MEIPASS  # PyInstaller bundle
        except AttributeError:
            _base = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
        logo_pix = QPixmap(os.path.join(_base, "assets", "zeno_logo.png"))
        if not logo_pix.isNull():
            self.ui.aboutLogoLabel.setPixmap(logo_pix.scaled(
                QSize(96, 96), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        apply_macos_styling(self)
        self._setup_gemini_section()
        self._apply_styles()
        QApplication.instance().paletteChanged.connect(
            lambda _: reapply_styles(self, self._apply_styles)
        )
        self._connect_signals()
        self.refresh()

    def _apply_styles(self):
        """Apply design-token styling. Re-runs on dark/light switch."""
        style_dialog(self)
        style_tab_widget(self.ui.tabWidget)
        style_table_widget(self.ui.fileTypesTable)
        style_group_box(self.ui.scheduleGroupBox)
        style_group_box(self.ui.geminiGroupBox)
        style_group_box(self.ui.startupGroupBox)
        style_group_box(self.ui.dateDefGroupBox)
        style_line_edit(self.ui.ruleExecIntervalEdit)
        style_line_edit(self.ui.geminiKeyEdit)
        style_combo_box(self.ui.geminiModelCombo)
        style_checkbox(self.ui.geminiEnableCheckBox)
        style_checkbox(self.ui.startAtLoginCheckBox)
        for rb in self.ui.dateDefGroupBox.findChildren(QRadioButton):
            style_radio_button(rb)
        style_secondary_btn(self.ui.geminiShowHideButton)
        style_loading_btn(self.ui.geminiTestButton)
        style_secondary_btn(self.ui.addFileTypeButton)
        ok_btn = self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn is not None:
            style_primary_btn(ok_btn)
        cancel_btn = self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_btn is not None:
            style_secondary_btn(cancel_btn)

    def _connect_signals(self):
        """One-time signal connections — called only from __init__."""
        self.ui.addFileTypeButton.clicked.connect(self.add_new_file_type)
        self.ui.fileTypesTable.cellChanged.connect(
            self.cell_changed, Qt.QueuedConnection)

    def _setup_gemini_section(self):
        """Hide AI section on non-macOS and wire up widgets."""
        if sys.platform != "darwin":
            self.ui.geminiGroupBox.setVisible(False)
            return
        
        # 1. SVG Icons for Show/Hide
        from PySide6.QtGui import QAction, QIcon, QPixmap, QColor, QPainter
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtCore import QByteArray
        
        def get_svg_icon(svg_str, color="#8e8e93"):
            svg_data = svg_str.replace('currentColor', color)
            renderer = QSvgRenderer(QByteArray(svg_data.encode('utf-8')))
            pixmap = QPixmap(20, 20)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            return QIcon(pixmap)

        eye_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>'
        eye_off_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>'
        
        color = C.text_secondary()
        self._icon_eye = get_svg_icon(eye_svg, color)
        self._icon_eye_off = get_svg_icon(eye_off_svg, color)

        # Integrate into the API key line edit
        self._toggle_action = QAction(self._icon_eye, "", self.ui.geminiKeyEdit)
        self._toggle_action.setCheckable(True)
        self._toggle_action.triggered.connect(self._on_gemini_show_hide)
        self.ui.geminiKeyEdit.addAction(self._toggle_action, QLineEdit.ActionPosition.TrailingPosition)

        # Remove the old separate Show button
        self.ui.geminiShowHideButton.setVisible(False)
        self.ui.geminiKeyLayout.removeWidget(self.ui.geminiShowHideButton)

        # Replace Test button with LoadingButton
        old_test_btn = self.ui.geminiTestButton
        # Find and remove old button from layout
        for i in range(self.ui.geminiModelLayout.count()):
            item = self.ui.geminiModelLayout.itemAt(i)
            if item.widget() == old_test_btn:
                self.ui.geminiModelLayout.removeItem(item)
                break
        old_test_btn.deleteLater()
        # Add new LoadingButton with stretch 1
        self.ui.geminiTestButton = LoadingButton("Test Connection", self.ui.geminiGroupBox)
        self.ui.geminiTestButton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.ui.geminiModelLayout.addWidget(self.ui.geminiTestButton, 1)

        # 2. Simple status label (hidden by default, shown only when there's a message)
        from PySide6.QtWidgets import QLabel
        self._status_label = QLabel(self.ui.geminiGroupBox)
        self._status_label.setWordWrap(True)
        self._status_label.setVisible(False)
        self.ui.verticalLayout_3.addWidget(self._status_label)

        for display, _ in MODEL_CHOICES.items():
            self.ui.geminiModelCombo.addItem(display)
        style_combo_box(self.ui.geminiModelCombo)
        # Remove fixed width so it expands to full width like API key
        self.ui.geminiModelCombo.setMinimumWidth(120)
        self.ui.geminiEnableCheckBox.toggled.connect(self._on_gemini_enabled_changed)
        self.ui.geminiTestButton.clicked.connect(self._on_gemini_test)

    def _on_gemini_enabled_changed(self, checked: bool):
        self.ui.geminiModelCombo.setEnabled(checked)
        self.ui.geminiKeyEdit.setEnabled(checked)
        self._toggle_action.setEnabled(checked)
        self.ui.geminiTestButton.setEnabled(checked)
        if not checked:
            self._status_label.setVisible(False)

    def _on_gemini_show_hide(self, checked: bool):
        echo = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.ui.geminiKeyEdit.setEchoMode(echo)
        self._toggle_action.setIcon(self._icon_eye_off if checked else self._icon_eye)

    def _on_gemini_test(self):
        key = self.ui.geminiKeyEdit.text().strip()
        if not key:
            self._set_status("Please Provide a Valid Gemini API Key", False)
            self.ui.geminiTestButton.show_error("No Key")
            return

        selected_model = self.ui.geminiModelCombo.currentText()
        if selected_model == "Select a Model Here":
            self._set_status("Please Select a Model From The List", False)
            self.ui.geminiTestButton.show_error("No Model")
            return

        self.ui.geminiTestButton.start_loading("Testing…")
        
        model_id = MODEL_CHOICES[self.ui.geminiModelCombo.currentText()]
        self._test_worker = _GeminiTestWorker(key, model_id, parent=self)
        self._test_worker.success.connect(self._on_gemini_test_success)
        self._test_worker.failure.connect(self._on_gemini_test_failure)
        self._test_worker.finished.connect(self._on_gemini_test_finished)
        self._test_worker.start()

    def _on_gemini_test_success(self):
        self._set_status("Connection successful", True)
        self.ui.geminiTestButton.show_success("Connected!")

    def _on_gemini_test_failure(self, message: str):
        self._set_status(message, False)
        self.ui.geminiTestButton.show_retry(5)

    def _on_gemini_test_finished(self):
        self._test_worker = None

    def _set_status(self, text: str, ok: bool | None):
        """Set status label text and visibility. Label is hidden when text is empty."""
        self._status_label.setText(text)
        if ok is True:
            style_status_label(self._status_label, status="success")
        elif ok is False:
            style_status_label(self._status_label, status="error")
        else:
            style_status_label(self._status_label, status="normal")
        # Only show the label if there's text
        self._status_label.setVisible(bool(text))


    def refresh(self):
        """Reload all widget values from current settings. Safe to call repeatedly."""
        self.settings = load_settings()

        # --- File types table ---
        self.ui.fileTypesTable.blockSignals(True)
        self.ui.fileTypesTable.setRowCount(0)
        i = 0
        self.format_fields = {}
        for f in self.settings['file_types']:
            self.ui.fileTypesTable.insertRow(i)
            item = QTableWidgetItem(f)
            if f in ('Audio', 'Video', 'Image'):
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            self.ui.fileTypesTable.setItem(i, 0, item)
            self.ui.fileTypesTable.setItem(
                i, 1, QTableWidgetItem(self.settings['file_types'][f]))

            # TBD: This increment is inside the loop, which is correct, but the comment was misleading.
            i += 1
        self.ui.fileTypesTable.blockSignals(False)

        # --- Date radio buttons ---
        rbs = [c for c in self.ui.dateDefGroupBox.children() if 'QRadioButton' in str(
            type(c))]  # TBD vN this is not very safe
        rbs[self.settings['date_type']].setChecked(True)
        self.ui.ruleExecIntervalEdit.setText(
            str(self.settings['rule_exec_interval']/60))
        
        try:
            self.ui.startAtLoginCheckBox.setChecked(startup_is_enabled())
        except Exception:
            self.ui.startAtLoginCheckBox.setChecked(False)

        if sys.platform == "darwin":
            self.ui.geminiKeyEdit.setText(self.settings.get("gemini_api_key", ""))
            model_id = self.settings.get("gemini_model", "gemini-3.1-flash-lite-preview")
            for i in range(self.ui.geminiModelCombo.count()):
                item_text = self.ui.geminiModelCombo.itemText(i)
                if item_text in MODEL_CHOICES and MODEL_CHOICES[item_text] == model_id:
                    self.ui.geminiModelCombo.setCurrentIndex(i)
                    break
            enabled = self.settings.get("gemini_enabled", False)
            self.ui.geminiEnableCheckBox.setChecked(enabled)
            self._on_gemini_enabled_changed(enabled)

    def cell_changed(self, row, col):
        if col == 0:
            settings = load_settings()
            new_value = self.ui.fileTypesTable.item(row, 0).text()
            other_values = [self.ui.fileTypesTable.item(i, 0).text() for i in range(
                self.ui.fileTypesTable.rowCount()) if self.ui.fileTypesTable.item(i, 0) and i != row]
            if new_value in other_values:  # settings['file_types'].keys():
                QMessageBox.critical(
                    self, "Error", "Duplicate format name, please change it")
                self.ui.fileTypesTable.editItem(
                    self.ui.fileTypesTable.item(row, 0))
                return False
            if row < len(settings['file_types']):  # it's not a new format
                prev_value = list(settings['file_types'].keys())[row]
                if new_value != prev_value and new_value:
                    
                    settings['file_types'][new_value] = settings['file_types'][prev_value]
                    del settings['file_types'][prev_value]
                    for i in range(len(settings['rules'])):
                        for k in range(len(settings['rules'][i]['conditions'])):
                            c = settings['rules'][i]['conditions'][k]
                            if c['type'] == 'type' and c['file_type'] == prev_value:
                                settings['rules'][i]['conditions'][k]['file_type'] = new_value
                    save_settings(settings)
                    self.settings = settings

                if new_value == "":
                    count = 0
                    for i in range(len(settings['rules'])):
                        for k in range(0, len(settings['rules'][i]['conditions'])):
                            c = settings['rules'][i]['conditions'][k]
                            if c['type'] == 'type' and c['file_type'] == prev_value:
                                count += 1
                    used_in_rules = "\nIt's used in " + \
                        str(count)+" condition(s) (which won't be removed)." if count > 0 else ""
                    # TBD remove orphaned conditions
                    reply = QMessageBox.question(self, "Warning",
                                                 "This will delete the format. Are you sure?"+used_in_rules,
                                                 QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        del settings['file_types'][prev_value]
                        save_settings(settings)
                        self.settings = settings
                        self.ui.fileTypesTable.removeRow(row)
                    else:
                        self.ui.fileTypesTable.item(row, 0).setText(prev_value)

    

    def add_new_file_type(self):
        """Adds a new empty row to the file types table for a new file type entry."""
        self.ui.fileTypesTable.insertRow(self.ui.fileTypesTable.rowCount())
        

    def accept(self):
        format_names = [self.ui.fileTypesTable.item(i, 0).text() for i in range(
            self.ui.fileTypesTable.rowCount()) if self.ui.fileTypesTable.item(i, 0)]
        if len(format_names) != len(set(format_names)):
            QMessageBox.critical(
                self, "Error", "Duplicate format name(s) detected, please remove duplicates")
            return False

        rbs = [c for c in self.ui.dateDefGroupBox.children()
               if 'QRadioButton' in str(type(c))]
        for c in rbs:
            if c.isChecked():
                self.settings['date_type'] = rbs.index(c)
        self.settings['rule_exec_interval'] = float(
            self.ui.ruleExecIntervalEdit.text())*60
        self.settings['file_types'] = {}
        # TBD add validation
        for i in range(self.ui.fileTypesTable.rowCount()):
            if self.ui.fileTypesTable.item(i, 0) and self.ui.fileTypesTable.item(i, 0).text():
                self.settings['file_types'][self.ui.fileTypesTable.item(
                    i, 0).text()] = self.ui.fileTypesTable.item(i, 1).text()

        try:
            want = self.ui.startAtLoginCheckBox.isChecked()
            if want:
                startup_enable()
            else:
                startup_disable()
        except Exception:
            pass

        if sys.platform == "darwin":
            self.settings["gemini_api_key"] = self.ui.geminiKeyEdit.text().strip()
            self.settings["gemini_model"] = MODEL_CHOICES[self.ui.geminiModelCombo.currentText()]
            self.settings["gemini_enabled"] = self.ui.geminiEnableCheckBox.isChecked()

        save_settings(self.settings)
        super(SettingsDialog, self).accept()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = SettingsDialog()
    

    sys.exit(app.exec())
