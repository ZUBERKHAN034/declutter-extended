import sys
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from src.ui.ui_condition_dialog import Ui_Condition
from src.ui.macos_style import apply_macos_styling

from declutter.store import load_settings


class ConditionDialog(QDialog):
    def __init__(self, parent=None):
        super(ConditionDialog, self).__init__(parent)

        self.ui = Ui_Condition()
        self.ui.setupUi(self)
        apply_macos_styling(self)
        self.condition = {}

        # Initial visibility
        self.update_visibility()

        self.ui.conditionCombo.currentIndexChanged.connect(self.update_visibility)

    def update_visibility(self):
        """
        Updates the visibility of UI elements based on the selected condition type.
        """
        state = self.ui.conditionCombo.currentText()

        self.ui.nameLabel.setVisible(state == "name")
        self.ui.nameCombo.setVisible(state == "name")
        self.ui.expressionLabel.setVisible(state == "name")
        self.ui.filemask.setVisible(state == "name")
        self.ui.filenameHint.setVisible(state == "name")

        self.ui.ageLabel.setVisible(state == "date")
        self.ui.ageCombo.setVisible(state == "date")
        self.ui.age.setVisible(state == "date")
        self.ui.ageUnitsCombo.setVisible(state == "date")

        self.ui.sizeLabel.setVisible(state == "size")
        self.ui.sizeCombo.setVisible(state == "size")
        self.ui.size.setVisible(state == "size")
        self.ui.sizeUnitsCombo.setVisible(state == "size")

        is_type = state == "type"
        self.ui.typeCombo.setVisible(is_type)
        self.ui.typeLabel.setVisible(is_type)
        self.ui.typeSwitchCombo.setVisible(is_type)

        # Re-populate the file-type picker every time it becomes active so it
        # always reflects the current list (handles fresh installs and types
        # added after the dialog was first constructed).
        if is_type:
            current_selection = self.ui.typeCombo.currentText()
            self.ui.typeCombo.blockSignals(True)
            self.ui.typeCombo.clear()
            file_type_names = list(load_settings()['file_types'].keys())
            self.ui.typeCombo.addItems(file_type_names)
            # Restore previous selection if still valid
            idx = self.ui.typeCombo.findText(current_selection)
            if idx >= 0:
                self.ui.typeCombo.setCurrentIndex(idx)
            self.ui.typeCombo.blockSignals(False)
            self.ui.typeCombo.setEnabled(True)
            self.ui.typeSwitchCombo.setEnabled(True)

    def load_condition(self, cond: dict = None):
        """
        Loads a condition into the dialog, populating the UI elements with the condition's data.
        """
        if cond is None:
            cond = {}
        self.condition = dict(cond)  # copy to avoid mutating external reference

        # Block signals to avoid intermediate visibility flicker while we set widgets
        self.ui.conditionCombo.blockSignals(True)
        try:
            if not cond:
                # Nothing to preload
                pass
            else:
                # Select condition type first
                self.ui.conditionCombo.setCurrentIndex(self.ui.conditionCombo.findText(cond.get('type', '')))
                ctype = cond.get('type')

                if ctype == 'name':
                    self.ui.nameCombo.setCurrentIndex(self.ui.nameCombo.findText(cond.get('name_switch', '')))
                    self.ui.filemask.setText(cond.get('filemask', ''))

                elif ctype == 'date':
                    self.ui.ageCombo.setCurrentIndex(self.ui.ageCombo.findText(cond.get('age_switch', '')))
                    self.ui.age.setText(str(cond.get('age', '')))
                    self.ui.ageUnitsCombo.setCurrentIndex(self.ui.ageUnitsCombo.findText(cond.get('age_units', '')))

                elif ctype == 'size':
                    self.ui.sizeCombo.setCurrentIndex(self.ui.sizeCombo.findText(cond.get('size_switch', '')))
                    self.ui.size.setText(str(cond.get('size', '')))
                    self.ui.sizeUnitsCombo.setCurrentIndex(self.ui.sizeUnitsCombo.findText(cond.get('size_units', '')))

                elif ctype == 'type':
                    self.ui.typeSwitchCombo.setCurrentIndex(self.ui.typeSwitchCombo.findText(cond.get('file_type_switch', '')))
                    self.ui.typeCombo.setCurrentIndex(self.ui.typeCombo.findText(cond.get('file_type', '')))
        finally:
            self.ui.conditionCombo.blockSignals(False)

        # 2) Force visibility refresh now that widgets are set
        self.update_visibility()

    def accept(self):
        error = ""

        ctype = self.ui.conditionCombo.currentText()
        self.condition['type'] = ctype

        if ctype == 'name':
            self.condition['name_switch'] = self.ui.nameCombo.currentText()
            if self.ui.filemask.text() == "":
                error = "Filemask can't be empty"
            self.condition['filemask'] = self.ui.filemask.text()

        elif ctype == 'date':
            self.condition['age_switch'] = self.ui.ageCombo.currentText()
            try:
                self.condition['age'] = float(self.ui.age.text())
            except Exception:
                error = "Incorrect Age value"
            self.condition['age_units'] = self.ui.ageUnitsCombo.currentText()

        elif ctype == 'size':
            self.condition['size_switch'] = self.ui.sizeCombo.currentText()
            try:
                self.condition['size'] = float(self.ui.size.text())
            except Exception:
                error = "Incorrect Size value"
            self.condition['size_units'] = self.ui.sizeUnitsCombo.currentText()

        elif ctype == 'type':
            self.condition['file_type_switch'] = self.ui.typeSwitchCombo.currentText()
            self.condition['file_type'] = self.ui.typeCombo.currentText()

        if error:
            QMessageBox.critical(self, "Error", error, QMessageBox.Ok)
        else:
            super(ConditionDialog, self).accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConditionDialog()
    window.show()
    sys.exit(app.exec())
