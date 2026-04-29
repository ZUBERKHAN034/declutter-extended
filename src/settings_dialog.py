from PySide6.QtWidgets import QDialog, QTableWidgetItem, QApplication, QMessageBox
from PySide6.QtCore import Qt, QSize
from declutter.config import VERSION
from declutter.store import load_settings, save_settings
from src.startup import is_enabled as startup_is_enabled, enable as startup_enable, disable as startup_disable

from src.ui.ui_settings_dialog import Ui_settingsDialog
from src.ui.macos_style import apply_macos_styling


class SettingsDialog(QDialog):
    def __init__(self):
        super(SettingsDialog, self).__init__()
        self.ui = Ui_settingsDialog()
        self.ui.setupUi(self)
        self.ui.aboutVersionLabel.setText(f"Version {VERSION}")
        from PySide6.QtGui import QPixmap
        self.ui.aboutLogoLabel.setPixmap(
            QPixmap(u":/images/icons/DeClutter_mac.png").scaled(
                QSize(80, 80), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        apply_macos_styling(self)
        self._connect_signals()
        self.refresh()

    def _connect_signals(self):
        """One-time signal connections — called only from __init__."""
        self.ui.addFileTypeButton.clicked.connect(self.add_new_file_type)
        self.ui.fileTypesTable.cellChanged.connect(
            self.cell_changed, Qt.QueuedConnection)

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

        save_settings(self.settings)
        super(SettingsDialog, self).accept()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = SettingsDialog()
    

    sys.exit(app.exec())
