import os
import sys
from copy import deepcopy
from time import time
import logging
import webbrowser
import requests

# --- macOS single-instance lock ---------------------------------------------------
_lock_handle = None  # kept alive to hold the file lock

def _resource_path(*parts):
    """Resolve a path relative to project root. Works in dev and in PyInstaller."""
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base, *parts)

def _ensure_single_instance():
    """Cross-platform single-instance guard using a lock file.

    On macOS, simply touching a PID file and checking for existing process
    with that PID is unreliable because PID reuse.  Instead, use an
    advisory flock on the lock file; this guarantees only one copy of the
    application can ever hold the lock, even across different log-in sessions.

    If another instance already holds the lock, silently exit."""
    import fcntl
    global _lock_handle
    lock_path = os.path.expanduser("~/.zeno.lock")
    _lock_handle = open(lock_path, "w")
    try:
        fcntl.flock(_lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        # Another instance is already running — exit silently
        sys.exit(0)
from PySide6.QtGui import QFontDatabase, QAction, QIcon, QFont, QPixmap, QPalette, QColor, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
    QDialog,
    QTableWidgetItem,
    QAbstractScrollArea,
    QTableWidgetSelectionRange,
    QMainWindow,
    QMessageBox,
)
from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot, QTimer, QByteArray
from src.rule_edit_window import RuleEditWindow
from src.settings_dialog import SettingsDialog
from src.ui.ui_rules_window import Ui_rulesWindow
from src.ui.ui_list_dialog import Ui_listDialog
from zeno.config import VERSION, LOG_FILE
from zeno.store import load_settings, save_settings
from zeno.rules import apply_all_rules, apply_rule, get_rule_by_id
from zeno.file_utils import open_file
from zeno.logging_utils import _refresh_log_file_handler

from src.ui.macos_style import apply_macos_styling, init_macos_theme
from zeno.ui.style_helpers import (
    style_dialog,
    style_table_widget,
    style_secondary_btn,
    style_primary_btn,
    style_toolbar,
    reapply_styles,
)
from zeno.ui.design_tokens import C

if sys.platform == "darwin":
    from zeno.ui.ai_rule_dialog import AIRuleDialog


class RulesWindow(QMainWindow):
    """Main application window for managing zenoing rules."""

    def __init__(self):
        super(RulesWindow, self).__init__()
        self.ui = Ui_rulesWindow()
        self.ui.setupUi(self)

        # Lock toolbar to top, disable moving/floating
        self.ui.toolBar.setMovable(False)
        self.ui.toolBar.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.ui.toolBar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        
        # Clear existing actions (including separators) and re-add to match screenshot
        self.ui.toolBar.clear()
        
        # Add a spacer widget on the left to push items to the center
        from PySide6.QtWidgets import QWidget, QSizePolicy
        spacer_left = QWidget()
        spacer_left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.ui.toolBar.addWidget(spacer_left)

        self.ui.toolBar.addAction(self.ui.actionAdd)
        self.ui.toolBar.addAction(self.ui.actionAddAI)
        self.ui.toolBar.addAction(self.ui.actionDelete)
        self.ui.toolBar.addAction(self.ui.actionExecute)
        self.ui.toolBar.addAction(self.ui.actionMove_up)
        self.ui.toolBar.addAction(self.ui.actionMove_down)
        self.ui.toolBar.addAction(self.ui.actionSettings)

        # Add a spacer widget on the right to complete the centering
        spacer_right = QWidget()
        spacer_right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.ui.toolBar.addWidget(spacer_right)

        self.ui.actionAdd.setText("Add Rule")
        self.ui.actionAddAI.setText("Magic Action")
        self.ui.actionDelete.setText("Delete Rule")
        self.ui.actionExecute.setText("Run Rule")
        self.ui.actionExecute.setFont(self.ui.actionAdd.font()) # Reset font to match others
        self.ui.actionMove_up.setText("Move Up")
        self.ui.actionMove_down.setText("Move Down")
        self.ui.actionSettings.setText("Quick Settings")

        self.minimizeAction = QAction()
        self.maximizeAction = QAction()
        self.restoreAction = QAction()
        self.quitAction = QAction()

        self.create_actions()
        self.create_tray_icon()
        self.settings = load_settings()

        # Restore geometry
        try:
            geom = self.settings.get("rules_window_geometry")
            if geom:
                ba = QByteArray(bytes(geom))
                self.restoreGeometry(ba)
        except Exception:
            pass

        apply_macos_styling(self)

        # Tag toolbar actions with their SVG resource paths so
        # recolor_toolbar_icons() can re-tint them on theme change.
        _icon_map = {
            self.ui.actionAdd: ":/images/icons/plus.svg",
            self.ui.actionAddAI: ":/images/icons/sparkle.svg",
            self.ui.actionDelete: ":/images/icons/trash.svg",
            self.ui.actionExecute: ":/images/icons/media-play.svg",
            self.ui.actionMove_up: ":/images/icons/arrow-thin-up.svg",
            self.ui.actionMove_down: ":/images/icons/arrow-thin-down.svg",
            self.ui.actionSettings: ":/images/icons/gear.svg",
        }
        for action, res in _icon_map.items():
            action.setProperty("_dc_icon_resource", res)

        # Apply initial icon colors for the current theme
        from src.ui.macos_style import recolor_icon
        dark = self.palette().color(QPalette.ColorRole.Window).lightness() < 128
        icon_color = QColor(255, 255, 255) if dark else QColor(30, 30, 30)
        for action, res in _icon_map.items():
            action.setIcon(recolor_icon(res, icon_color))

        self._apply_styles()
        QApplication.instance().paletteChanged.connect(
            lambda _: reapply_styles(self, self._apply_styles)
        )

        self.ui.addRule.clicked.connect(self.add_rule)
        self.load_rules()
        self.ui.rulesTable.cellDoubleClicked.connect(self.edit_rule)
        self.ui.deleteRule.clicked.connect(self.delete_rule)
        self.ui.applyRule.clicked.connect(self.apply_rule)
        self.setWindowIcon(QIcon(_resource_path("assets", "zeno_logo.png")))
        self.trayIcon.messageClicked.connect(self.message_clicked)
        self.trayIcon.activated.connect(self.tray_activated)
        self.trayIcon.setToolTip(
            "Zeno runs every "
            + str(float(self.settings["rule_exec_interval"] / 60))
            + " minute(s)"
        )
        self.service_run_details = []
        # TBD: self.start_thread() - check if this is needed

        # Hide UI elements related to rule management (TBD: Re-evaluate visibility based on user roles/features)
        self.ui.addRule.setVisible(False)
        self.ui.applyRule.setVisible(False)
        self.ui.deleteRule.setVisible(False)
        self.ui.moveUp.setVisible(False)
        self.ui.moveDown.setVisible(False)

        self.ui.actionAdd.triggered.connect(self.add_rule)
        if sys.platform == "darwin":
            self.ui.actionAddAI.triggered.connect(self.add_ai_rule)
            self._ai_dialog = AIRuleDialog(parent=self)
            self._ai_dialog.rule_generated.connect(self._on_ai_rule_generated)
            self._ai_dialog.open_settings_requested.connect(self.show_settings)
        else:
            self.ui.actionAddAI.setVisible(False)
        self.ui.actionDelete.triggered.connect(self.delete_rule)
        self.ui.actionExecute.triggered.connect(self.apply_rule)
        self.ui.actionOpen_log_file.triggered.connect(self.open_log_file)
        self.ui.actionClear_log_file.triggered.connect(self.clear_log_file)
        self.ui.actionSettings.setMenuRole(QAction.MenuRole.NoRole)
        self.ui.actionSettings.setShortcut(QKeySequence.StandardKey.Preferences)
        self.ui.actionSettings.triggered.connect(self.show_settings)
        self.ui.actionAbout.triggered.connect(self.show_about)
        self._settings_dialog = SettingsDialog()
        self._settings_dialog.accepted.connect(self._on_settings_saved)
        self._settings_dialog.finished.connect(self._on_settings_closed)

        self.ui.actionMove_up.triggered.connect(self.move_rule_up)
        self.ui.actionMove_down.triggered.connect(self.move_rule_down)

        self.service_runs = False

        self.timer = QTimer(self)
        self.timer.setInterval(int(self.settings["rule_exec_interval"] * 1000))
        self.timer.timeout.connect(self.start_thread)
        self.timer.start()

        self.instanced_thread = new_version_checker(self)
        self.instanced_thread.start()
        self.instanced_thread.version.connect(self.suggest_download)

    def _apply_styles(self):
        """Apply design-token styling. Re-runs on dark/light switch."""
        style_dialog(self)
        style_table_widget(self.ui.rulesTable)
        style_toolbar(self.ui.toolBar)

    def suggest_download(self, version):
        """Suggests downloading a new version of the application if available."""
        if version:
            try:
                from packaging.version import Version

                current_version = Version(load_settings()["version"])
                # Normalize GitHub version (remove 'v' prefix if present)
                latest_version = Version(version.lstrip("v"))

                if latest_version > current_version:
                    reply = QMessageBox.question(
                        self,
                        f"New version: {latest_version}",
                        r"There's a new version of Zeno available. Download now?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply == QMessageBox.Yes:
                        try:
                            webbrowser.open(
                                "https://github.com/midnightdim/zeno/releases/latest"
                            )
                        except Exception as e:
                            logging.exception(f"exception {e}")
            except Exception as e:
                logging.exception(f"Version comparison failed: {e}")

    def tray_activated(self, reason):
        """Handles activation of the system tray icon."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.setVisible(True)

    def move_rule_up(self):
        """Moves the selected rule up in the list."""
        rule_idx = self.ui.rulesTable.selectedIndexes()[0].row()
        if rule_idx:
            rule_id = int(self.settings["rules"][rule_idx]["id"])
            self.settings["rules"][rule_idx]["id"] = self.settings["rules"][
                rule_idx - 1
            ]["id"]
            self.settings["rules"][rule_idx - 1]["id"] = rule_id

            rules = deepcopy(self.settings["rules"])
            rule_ids = [int(r["id"]) for r in rules if "id" in r.keys()]
            rule_ids.sort()

            self.settings["rules"] = []
            i = 0
            for rule_id in rule_ids:
                i += 1
                rule = get_rule_by_id(rule_id, rules)
                rule["id"] = i  # renumbering rules
                self.settings["rules"].append(rule)

            save_settings(self.settings)
            self.load_rules()
            self.ui.rulesTable.selectRow(rule_idx - 1)

    def move_rule_down(self):
        """Moves the selected rule down in the list."""
        rule_idx = self.ui.rulesTable.selectedIndexes()[0].row()
        if rule_idx < self.ui.rulesTable.rowCount() - 1:
            rule_id = int(self.settings["rules"][rule_idx]["id"])
            self.settings["rules"][rule_idx]["id"] = self.settings["rules"][
                rule_idx + 1
            ]["id"]
            self.settings["rules"][rule_idx + 1]["id"] = rule_id

            rules = deepcopy(self.settings["rules"])
            rule_ids = [int(r["id"]) for r in rules if "id" in r.keys()]
            rule_ids.sort()

            self.settings["rules"] = []
            i = 0
            for rule_id in rule_ids:
                i += 1
                rule = get_rule_by_id(rule_id, rules)
                rule["id"] = i  # renumbering rules
                self.settings["rules"].append(rule)

            save_settings(self.settings)
            self.load_rules()
            self.ui.rulesTable.selectRow(rule_idx + 1)

    def show_about(self):
        """Shows the application's About box."""
        QMessageBox.about(
            self,
            "About Zeno",
            "Zeno version "
            + str(VERSION)
            + "\nhttps://github.com/midnightdim/zeno\nAuthor: Dmitry Beloglazov\nTelegram: @beloglazov",
        )

    def show_settings(self):
        """Shows the settings dialog (reuses a single instance)."""
        _set_macos_activation_policy(False)
        self._settings_dialog.refresh()
        self._settings_dialog.show()
        self._settings_dialog.raise_()
        self._settings_dialog.activateWindow()

    def _on_settings_saved(self):
        """Slot called when the Settings dialog is accepted (OK/Save)."""
        self.settings = load_settings()
        self.trayIcon.setToolTip(
            "Zeno runs every "
            + str(float(self.settings["rule_exec_interval"] / 60))
            + " minute(s)"
        )
        self.timer.setInterval(int(self.settings["rule_exec_interval"] * 1000))

    def _on_settings_closed(self):
        """Slot called when the Settings dialog is dismissed (OK or Cancel)."""
        if not self.isVisible():
            _set_macos_activation_policy(True)

    def open_log_file(self):
        """Opens the log file."""
        open_file(LOG_FILE)

    def clear_log_file(self):
        reply = QMessageBox.question(
            self,
            "Warning",
            "Are you sure you want to clear the log?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                _refresh_log_file_handler()  # detach/close existing handler
                with open(LOG_FILE, "w", encoding="utf-8"):
                    pass  # truncate
                _refresh_log_file_handler(mode="a+")  # reattach so logging continues
                logging.info("Log file cleared.")
            except Exception as e:
                logging.exception(f"exception {e}")

    def message_clicked(self):
        """Shows a dialog with details about the last service run."""
        msgBox = QDialog(self)
        msgBox.ui = Ui_listDialog()
        msgBox.ui.setupUi(msgBox)
        msgBox.setWindowTitle("Rule executed")
        affected = self.service_run_details
        if affected:
            msgBox.ui.label.setText(
                str(len(affected)) + " file(s) affected by this rule:"
            )
            msgBox.ui.listWidget.addItems(affected)
        else:
            msgBox.ui.listWidget.setVisible(False)
            msgBox.ui.label.setText("No files affected by this rule.")
        msgBox.exec()
        self.service_run_details = []

    def start_thread(self):
        """Starts the zeno service thread if it is not already running."""
        if not self.service_runs:
            self.service_runs = True
            instanced_thread = zeno_service(self)
            instanced_thread.start()
        else:
            logging.debug("Service still running, skipping the scheduled exec")

    def add_rule(self):
        """Opens the rule edit window to add a new rule."""
        self.rule_window = RuleEditWindow()
        if self.rule_window.exec():
            rule = self.rule_window.rule
            rule["id"] = (
                max([int(r["id"]) for r in self.settings["rules"] if "id" in r.keys()])
                + 1
                if self.settings["rules"]
                else 1
            )
            self.settings["rules"].append(rule)
        save_settings(self.settings)
        self.load_rules()

    def add_ai_rule(self):
        """Opens the AI rule generation dialog."""
        self._ai_dialog.show()
        self._ai_dialog.raise_()
        self._ai_dialog.activateWindow()

    def _on_ai_rule_generated(self, rule: dict):
        """Open rule editor pre-populated with AI-generated rule for review."""
        self.rule_window = RuleEditWindow()
        self.rule_window.setWindowTitle("Review AI Generated Rule")
        self.rule_window.load_rule(rule)
        if self.rule_window.exec():
            rule = self.rule_window.rule
            rule["id"] = (
                max([int(r["id"]) for r in self.settings["rules"] if "id" in r.keys()])
                + 1
                if self.settings["rules"]
                else 1
            )
            self.settings["rules"].append(rule)
            save_settings(self.settings)
            self.load_rules()
            self._ai_dialog.accept()
        else:
            self._ai_dialog.show()
            self._ai_dialog.raise_()
            self._ai_dialog.activateWindow()

    def edit_rule(self, r, c):
        """Opens the rule edit window to edit the selected rule."""
        if c == 1:  # Enabled/Disabled is clicked
            self.settings["rules"][r]["enabled"] = not self.settings["rules"][r][
                "enabled"
            ]
            save_settings(self.settings)
        else:
            rule = deepcopy(self.settings["rules"][r])
            self.rule_window = RuleEditWindow()
            self.rule_window.load_rule(rule)
            if self.rule_window.exec():
                self.settings["rules"][r] = self.rule_window.rule
        save_settings(self.settings)
        self.load_rules()

    def delete_rule(self):
        """Deletes the selected rule(s)."""
        # selectedIndexes() returns one index per cell, so we need unique row numbers
        del_indexes = list(set([r.row() for r in self.ui.rulesTable.selectedIndexes()]))

        if del_indexes:
            del_names = [
                r["name"]
                for r in self.settings["rules"]
                if self.settings["rules"].index(r) in del_indexes
            ]

            reply = QMessageBox.question(
                self,
                "Warning",
                "Are you sure you want to delete selected rules:\n"
                + "\n".join(del_names)
                + "\n?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                # Delete in reverse order so we don't invalidate earlier indexes
                for ind in sorted(del_indexes, reverse=True):
                    del self.settings["rules"][ind]
                    self.ui.rulesTable.removeRow(ind)

                # Persist the changes so rules don't come back!
                save_settings(self.settings)

                self.ui.rulesTable.clearSelection()

    def apply_rule(self):
        """Applies the selected rule."""
        selected = self.ui.rulesTable.selectedIndexes()
        if not selected:
            QMessageBox.warning(self, "No rule selected", "Please select a rule first.")
            return

        rule = deepcopy(self.settings["rules"][selected[0].row()])
        rule["enabled"] = True
        report, affected = apply_rule(rule)

        msgBox = QDialog(self)
        msgBox.ui = Ui_listDialog()
        msgBox.ui.setupUi(msgBox)
        msgBox.setWindowTitle("Rule executed")

        if affected:
            msgBox.ui.label.setText(
                str(len(affected)) + " file(s) affected by this rule:"
            )
            msgBox.ui.listWidget.addItems(affected)
        else:
            msgBox.ui.listWidget.setVisible(False)
            msgBox.ui.label.setText("No files affected by this rule.")
        msgBox.exec()

    def load_rules(self):
        """Loads settings (including rules) from the store and populates the rules table."""
        self.settings = load_settings()

        rules = [(int(r["id"]), r) for r in self.settings["rules"] if "id" in r]
        rules.sort(key=lambda y: y[0])

        self.ui.rulesTable.setRowCount(len(rules))
        for i, (_, rule) in enumerate(rules):
            self.ui.rulesTable.setItem(i, 0, QTableWidgetItem(rule["name"]))
            status_item = QTableWidgetItem("Enabled" if rule["enabled"] else "Disabled")
            status_item.setForeground(QColor(C.success() if rule["enabled"] else C.error()))
            self.ui.rulesTable.setItem(i, 1, status_item)
            self.ui.rulesTable.setItem(i, 2, QTableWidgetItem(rule["action"]))
            self.ui.rulesTable.setItem(
                i, 3, QTableWidgetItem(",".join(rule["folders"]))
            )

        self.ui.rulesTable.setColumnWidth(0, 200)
        self.ui.rulesTable.setColumnWidth(1, 100)
        self.ui.rulesTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

    def create_actions(self):
        """Creates the actions for the tray icon menu."""
        self.showRulesWindow = QAction("Rules", self)
        self.showRulesWindow.triggered.connect(self.showNormal)

        self.showSettingsWindow = QAction("Settings", self)
        self.showSettingsWindow.setMenuRole(QAction.MenuRole.NoRole)
        self.showSettingsWindow.triggered.connect(self.show_settings)

        self.quitAction = QAction("Quit", self)
        # self.quitAction.triggered.connect(QApplication.quit)
        self.quitAction.triggered.connect(self._handle_quit)

    def create_tray_icon(self):
        """Creates the system tray icon and its context menu."""
        if getattr(self, '_tray_initialized', False):
            return
        self._tray_initialized = True

        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.addAction(self.showRulesWindow)
        self.trayIconMenu.addAction(self.showSettingsWindow)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.quitAction)

        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        _tray_icon = QIcon(_resource_path("assets", "icons", "tray.svg"))
        _tray_icon.setIsMask(True)
        self.trayIcon.setIcon(_tray_icon)
        self.trayIcon.setVisible(True)
        self.trayIcon.show()

    def setVisible(self, visible):
        """Sets the visibility of the main window and updates the tray icon actions accordingly."""
        self.minimizeAction.setEnabled(visible)
        self.maximizeAction.setEnabled(not self.isMaximized())
        self.restoreAction.setEnabled(self.isMaximized() or not visible)
        super().setVisible(visible)

    def _handle_quit(self):
        # Mark that we are quitting, then initiate app shutdown
        app = QApplication.instance()
        if app is not None:
            app.setProperty("will_quit", True)
        QApplication.quit()

    def showEvent(self, e):
        # Ensure a user-shown window will be shown next startup
        _set_macos_activation_policy(False)
        try:
            s = load_settings()
            s["rules_window_visible_on_exit"] = True
            save_settings(s)
        except Exception:
            pass
        super().showEvent(e)

    def hideEvent(self, e):
        """
        Hide to tray. Only set next-start visibility to False if not quitting.
        """
        app = QApplication.instance()
        will_quit = bool(app.property("will_quit")) if app is not None else False

        if will_quit:
            super().hideEvent(e)
            return

        try:
            s = load_settings()
            s["rules_window_visible_on_exit"] = False
            s["rules_window_geometry"] = list(bytes(self.saveGeometry()))
            save_settings(s)
        except Exception:
            pass
        super().hideEvent(e)
        _set_macos_activation_policy(True)

    def closeEvent(self, event):
        """
        Persist final state before application quits or the window is closed.
        """
        app = QApplication.instance()
        will_quit = bool(app.property("will_quit")) if app is not None else False

        try:
            s = load_settings()
            s["rules_window_geometry"] = list(bytes(self.saveGeometry()))
            if will_quit:
                # On explicit quit, record actual visibility at the moment we initiated quit
                s["rules_window_visible_on_exit"] = self.isVisible()
            # Else: leave visibility to hideEvent (X-to-tray flow)
            save_settings(s)
        except Exception:
            pass
        super().closeEvent(event)

    @Slot(str, list)
    def show_tray_message(self, message, details):
        """Shows a message in the system tray."""
        if message:
            self.trayIcon.showMessage(
                "Zeno",
                message,
                QIcon(_resource_path("assets", "icons", "info.svg")),
                15000,
            )

        self.service_run_details = details if details else self.service_run_details
        self.service_runs = False


class service_signals(QObject):
    signal1 = Signal(str, list)


class zeno_service(QThread):
    """A QThread subclass for running Zeno rules in the background."""

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.signals = service_signals()
        self.signals.signal1.connect(parent.show_tray_message)
        self.starting_seconds = time()

    def run(self):
        try:
            details = []
            report, details = apply_all_rules(load_settings())
            msg = ""
            for key in report.keys():
                msg += key + ": " + str(report[key]) + "\n" if report[key] > 0 else ""
            if len(msg) > 0:
                msg = "Processed files and folders:\n" + msg
            self.signals.signal1.emit(msg, details)
        except Exception as e:
            logging.exception(f"Scheduled rule execution failed: {e}")
            self.signals.signal1.emit("", [])


class new_version_checker(QThread):
    """A QThread subclass for checking for new versions of Zeno."""

    version = Signal(str)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)

    def run(self):
        try:
            response = requests.get(
                "https://api.github.com/repos/midnightdim/zeno/releases/latest"
            )
            if response.status_code == 200:
                latest_version = response.json()["tag_name"]
                self.version.emit(latest_version.strip())
        except Exception as e:
            logging.exception(f"exception {e}")


def _set_macos_activation_policy(accessory: bool):
    """Switch NSApplication activation policy.
    accessory=True hides the Dock icon; accessory=False shows it.
    """
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyAccessory, NSApplicationActivationPolicyRegular
        ns_app = NSApplication.sharedApplication()
        policy = NSApplicationActivationPolicyAccessory if accessory else NSApplicationActivationPolicyRegular
        ns_app.setActivationPolicy_(policy)
    except Exception:
        pass

def main():
    """Main function to run the application."""
    _ensure_single_instance()

    app = QApplication(sys.argv)
    QApplication.setQuitOnLastWindowClosed(False)

    if sys.platform == "darwin":
        app.setStyle("Fusion")
        from PySide6.QtGui import QFont
        app.setFont(QFont("SF Pro Text", 13))

    from zeno.store import init_store

    init_store()
    logging.info("Zeno started")
    app.setWindowIcon(QIcon(_resource_path("assets", "zeno_logo.png")))
    # Override the Dock icon via NSApplication so the Python rocket
    # does not appear when running from source (non-bundle).
    try:
        from AppKit import NSApplication, NSImage
        ns_app = NSApplication.sharedApplication()
        icon_path = _resource_path("assets", "zeno_logo.icns")
        icon_path = os.path.normpath(icon_path)
        image = NSImage.alloc().initWithContentsOfFile_(icon_path)
        if image:
            ns_app.setApplicationIconImage_(image)
    except ImportError:
        logging.warning(
            "AppKit not available — Dock icon will show the Python rocket. "
            "Activate the virtualenv (source venv/bin/activate) to load pyobjc."
        )
    except Exception:
        pass

    # Apply system dark/light palette and wire paletteChanged so the
    # app follows macOS appearance changes live.
    init_macos_theme(app)

    window = RulesWindow()

    # Clean up tray icon on quit so a stale icon never lingers
    def _cleanup_tray():
        if hasattr(window, 'trayIcon') and window.trayIcon is not None:
            window.trayIcon.hide()
            window.trayIcon.deleteLater()
    app.aboutToQuit.connect(_cleanup_tray)

    # Decide visibility based on persisted flag
    settings = load_settings()
    if settings["rules_window_visible_on_exit"]:
        window.show()
    else:
        _set_macos_activation_policy(True)

    window.setWindowTitle("Rules")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
