"""Dialog to generate a DeClutter rule from natural language using Gemini AI."""

import os
import sys
from typing import Any, Dict, List

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QDialogButtonBox,
    QWidget,
)
from PySide6.QtCore import Qt, QThread, Signal as _Signal, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QGraphicsOpacityEffect

from declutter.store import load_settings, list_file_types, list_rules
from src.ui.macos_style import button_stylesheet

_EXAMPLES = [
    "Move all PDFs older than 7 days to a Documents folder",
    "Delete files in Downloads larger than 1GB",
    "Move screenshots to a Screenshots folder on Desktop",
    "Trash any file that hasn't been modified in 90 days",
    "Copy images to Pictures and keep originals",
    "Move zip files older than 30 days to Archives",
]


class ExamplesBanner(QWidget):
    """Cross-fading banner that shows one example at a time."""

    example_clicked = _Signal(str)

    EXAMPLES = [
        "Move all PDFs older than 7 days to a Documents folder",
        "Delete files in Downloads larger than 1GB",
        "Move screenshots to a Screenshots folder on Desktop",
        "Trash any file that hasn't been modified in 90 days",
        "Copy images to Pictures and keep originals",
        "Move zip files older than 30 days to Archives",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self._current_index = 0

        # Two overlapping labels for crossfade
        self._label_a = QLabel(self)
        self._label_b = QLabel(self)

        for label in (self._label_a, self._label_b):
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setGeometry(self.rect())
            label.setCursor(Qt.CursorShape.PointingHandCursor)
            label.setTextFormat(Qt.TextFormat.RichText)
            label.mousePressEvent = self._on_click

        # Set initial text
        self._label_a.setText(self._format_example(self.EXAMPLES[0]))
        self._label_b.hide()

        # Opacity effects for crossfade
        self._effect_a = QGraphicsOpacityEffect(self._label_a)
        self._effect_b = QGraphicsOpacityEffect(self._label_b)
        self._label_a.setGraphicsEffect(self._effect_a)
        self._label_b.setGraphicsEffect(self._effect_b)
        self._effect_a.setOpacity(1.0)
        self._effect_b.setOpacity(0.0)

        # Animations
        self._fade_out = QPropertyAnimation(self._effect_a, b"opacity")
        self._fade_in = QPropertyAnimation(self._effect_b, b"opacity")
        for anim in (self._fade_out, self._fade_in):
            anim.setDuration(400)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._fade_out.finished.connect(self._on_fade_out_done)

        # Auto-advance timer
        self._timer = QTimer(self)
        self._timer.setInterval(3000)  # 3 seconds
        self._timer.timeout.connect(self._next_example)
        self._timer.start()

        self._active_label = self._label_a
        self._inactive_label = self._label_b
        self._active_effect = self._effect_a
        self._inactive_effect = self._effect_b

    def _next_example(self):
        self._current_index = (self._current_index + 1) % len(self.EXAMPLES)

        # Set next text on inactive label and show it
        self._inactive_label.setText(
            self._format_example(self.EXAMPLES[self._current_index])
        )
        self._inactive_label.show()

        # Fade out active, fade in inactive
        self._fade_out.setTargetObject(self._active_effect)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)

        self._fade_in.setTargetObject(self._inactive_effect)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)

        self._fade_out.start()
        self._fade_in.start()

    def _on_fade_out_done(self):
        # Swap active and inactive labels
        self._active_label.hide()
        self._active_label, self._inactive_label = (
            self._inactive_label, self._active_label
        )
        self._active_effect, self._inactive_effect = (
            self._inactive_effect, self._active_effect
        )

    def _on_click(self, event):
        # Fill prompt with current example (without "e.g. ")
        self.example_clicked.emit(self.EXAMPLES[self._current_index])
        # Pause auto-advance briefly after click
        self._timer.stop()
        QTimer.singleShot(5000, self._timer.start)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for label in (self._label_a, self._label_b):
            label.setGeometry(self.rect())

    def hideEvent(self, event):
        super().hideEvent(event)
        self._timer.stop()

    def _format_example(self, text: str) -> str:
        is_dark = QApplication.instance().palette().color(
            QPalette.ColorRole.Window
        ).lightness() < 128

        prefix_color = "#4a9eff" if is_dark else "#0066cc"
        text_color = "#aaaaaa" if is_dark else "#666666"

        return (
            f'<span style="color:{prefix_color}; '
            f'font-weight:600;">Try →</span> '
            f'<span style="color:{text_color}; '
            f'font-style:italic;">{text}</span>'
        )

    def _apply_label_style(self):
        current = self.EXAMPLES[self._current_index]
        self._active_label.setText(self._format_example(current))

    def showEvent(self, event):
        super().showEvent(event)
        self._timer.start()

if sys.platform == "darwin":
    from declutter.ai.gemini_service import GeminiService, MODEL_CHOICES, is_ai_available


# ---------------------------------------------------------------------------
# Worker thread
# ---------------------------------------------------------------------------

class _GenerateRuleWorker(QThread):
    """Background thread that calls Gemini to generate a rule."""

    success = _Signal(dict)
    failure = _Signal(str)

    def __init__(
        self,
        api_key: str,
        model: str,
        prompt: str,
        context: dict,
        parent=None,
    ):
        super().__init__(parent)
        self._api_key = api_key
        self._model = model
        self._prompt = prompt
        self._context = context

    def run(self):
        try:
            svc = GeminiService(self._api_key, model=self._model)
            rule = svc.generate_rule(self._prompt, self._context)
            self.success.emit(rule)
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            self.failure.emit(msg)


# ---------------------------------------------------------------------------
# Format conversion helpers
# ---------------------------------------------------------------------------


def _parse_value_with_unit(value_str: str) -> tuple:
    """Split a string like '30 days' or '100 MB' into (number, unit)."""
    parts = value_str.strip().split(None, 1)
    if len(parts) == 2:
        try:
            return float(parts[0]), parts[1]
        except ValueError:
            pass
    # Fallback: try to extract leading number
    numeric = ""
    rest = ""
    for ch in value_str.strip():
        if ch.isdigit() or ch == "." and numeric.count(".") == 0:
            numeric += ch
        else:
            rest = value_str.strip()[len(numeric):].strip()
            break
    return (float(numeric) if numeric else 0.0), rest or "days"


def _convert_gemini_rule_to_app(gemini_rule: dict) -> dict:
    """Convert the JSON schema returned by Gemini into DeClutter's internal rule dict."""
    # Sources → folders + recursive
    sources = gemini_rule.get("sources", [])
    folders: List[str] = []
    recursive = False
    if sources:
        folders = [s["path"] for s in sources if isinstance(s, dict) and "path" in s]
        if sources[0] and isinstance(sources[0], dict):
            recursive = bool(sources[0].get("recursive", False))

    # Conditions
    raw_conditions = gemini_rule.get("conditions", [])
    conditions: List[Dict[str, Any]] = []
    for rc in raw_conditions:
        field = rc.get("field", "")
        operator = rc.get("operator", "")
        value = rc.get("value", "")

        if field == "type":
            conditions.append({
                "type": "type",
                "file_type_switch": operator,
                "file_type": value,
            })
        elif field == "name":
            conditions.append({
                "type": "name",
                "name_switch": operator,
                "filemask": value,
            })
        elif field == "date":
            age, age_units = _parse_value_with_unit(str(value))
            conditions.append({
                "type": "date",
                "age_switch": operator,
                "age": age,
                "age_units": age_units,
            })
        elif field == "size":
            size, size_units = _parse_value_with_unit(str(value))
            conditions.append({
                "type": "size",
                "size_switch": operator,
                "size": size,
                "size_units": size_units,
            })

    # Actions — app supports a single action per rule
    raw_actions = gemini_rule.get("actions", [])
    action = "Move"
    target_folder = ""
    target_subfolder = ""
    name_pattern = ""
    if raw_actions:
        first = raw_actions[0]
        act_type = first.get("type", "move")
        target = first.get("target", "")
        if act_type == "move":
            action = "Move"
            target_folder = target
        elif act_type == "copy":
            action = "Copy"
            target_folder = target
        elif act_type == "delete":
            action = "Delete"
        elif act_type == "trash":
            action = "Trash"
        elif act_type == "rename":
            action = "Rename"
            name_pattern = target
        elif act_type == "move_to_subfolder":
            action = "Move to subfolder"
            target_subfolder = target

    return {
        "name": gemini_rule.get("name", ""),
        "enabled": bool(gemini_rule.get("enabled", True)),
        "action": action,
        "recursive": recursive,
        "condition_switch": gemini_rule.get("match_mode", "all"),
        "keep_tags": False,
        "keep_folder_structure": False,
        "target_folder": target_folder,
        "target_subfolder": target_subfolder,
        "name_pattern": name_pattern,
        "overwrite_switch": "increment name",
        "ignore_newest": False,
        "ignore_N": "",
        "folders": folders,
        "conditions": conditions,
    }


def _human_readable_summary(rule: dict) -> str:
    """Return a concise, human-readable summary of an app-format rule."""
    lines: List[str] = []
    lines.append(f"Name: {rule.get('name', 'Unnamed')}")

    folders = rule.get("folders", [])
    if folders:
        folders_str = ", ".join(folders)
        rec = "Yes" if rule.get("recursive") else "No"
        lines.append(f"Source: {folders_str} (recursive: {rec})")
    else:
        lines.append("Source: (none)")

    lines.append(f"Match mode: {rule.get('condition_switch', 'all')} conditions must match")

    conditions = rule.get("conditions", [])
    if conditions:
        lines.append("Conditions:")
        for c in conditions:
            ctype = c.get("type", "")
            if ctype == "type":
                lines.append(f"  - File type {c.get('file_type_switch', 'is')} {c.get('file_type', '')}")
            elif ctype == "name":
                lines.append(f"  - Name {c.get('name_switch', 'matches')} {c.get('filemask', '')}")
            elif ctype == "date":
                lines.append(
                    f"  - Age is {c.get('age_switch', '')} "
                    f"{c.get('age', '')} {c.get('age_units', '')}"
                )
            elif ctype == "size":
                lines.append(
                    f"  - File size is {c.get('size_switch', '')} "
                    f"{c.get('size', '')}{c.get('size_units', '')}"
                )
            else:
                lines.append(f"  - {c}")
    else:
        lines.append("Conditions: (none)")

    action = rule.get("action", "Move")
    if action in ("Move", "Copy"):
        lines.append(f"Action: {action} to {rule.get('target_folder', '')}")
    elif action == "Move to subfolder":
        lines.append(f"Action: Move to subfolder {rule.get('target_subfolder', '')}")
    elif action == "Rename":
        lines.append(f"Action: Rename to pattern {rule.get('name_pattern', '')}")
    else:
        lines.append(f"Action: {action}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main dialog
# ---------------------------------------------------------------------------

class AIRuleDialog(QDialog):
    """Dialog that lets the user describe a rule in English and generates it via Gemini."""

    rule_generated = _Signal(dict)
    open_settings_requested = _Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Rule with AI")
        self.setMinimumSize(520, 420)

        self._worker: _GenerateRuleWorker | None = None
        self._generated_rule: dict | None = None

        self._build_ui()
        self._apply_styling()
        self._check_ai_availability()

    # -- UI construction --------------------------------------------------

    def _build_ui(self):
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setSpacing(12)
        self._main_layout.setContentsMargins(20, 20, 20, 20)

        # ---- Content widget (normal flow) --------------------------------
        self._content = QWidget()
        layout = QVBoxLayout(self._content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Title label
        title = QLabel("Describe what you want")
        font = title.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2)
        title.setFont(font)
        layout.addWidget(title)

        # Description input
        self._desc_edit = QTextEdit()
        self._desc_edit.setPlaceholderText(_EXAMPLES[0])
        self._desc_edit.setMaximumHeight(80)
        layout.addWidget(self._desc_edit)

        # Cross-fading examples banner
        self._examples_banner = ExamplesBanner()
        self._examples_banner.example_clicked.connect(self._on_example_clicked)
        layout.addWidget(self._examples_banner)

        # Generate button row
        gen_row = QHBoxLayout()
        self._generate_btn = QPushButton("Generate Rule")
        self._generate_btn.setDefault(True)
        self._generate_btn.clicked.connect(self._on_generate)
        gen_row.addWidget(self._generate_btn)

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        gen_row.addWidget(self._status_label, 1)
        gen_row.addStretch()
        layout.addLayout(gen_row)

        # Preview area
        preview_title = QLabel("Preview")
        preview_title.setFont(font)
        layout.addWidget(preview_title)

        self._preview_edit = QTextEdit()
        self._preview_edit.setReadOnly(True)
        self._preview_edit.setPlaceholderText("Generated rule preview will appear here…")
        self._preview_edit.setMinimumHeight(120)
        self._preview_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._preview_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self._preview_edit, 1)

        # Dialog buttons
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.Cancel | QDialogButtonBox.Ok
        )
        self._button_box.button(QDialogButtonBox.Ok).setText("Open in Editor")
        self._button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self._button_box.accepted.connect(self._on_add_rule)
        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box)

        self._main_layout.addWidget(self._content)

        # ---- No-API-key widget -------------------------------------------
        self._no_key_widget = QWidget()
        no_key_layout = QVBoxLayout(self._no_key_widget)
        no_key_layout.setContentsMargins(0, 40, 0, 40)
        no_key_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._no_key_msg = QLabel(
            "Set your Gemini API key in Settings to use this feature."
        )
        self._no_key_msg.setWordWrap(True)
        self._no_key_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_key_layout.addWidget(self._no_key_msg)

        self._open_settings_btn = QPushButton("Open Settings")
        self._open_settings_btn.clicked.connect(self._on_open_settings)
        no_key_layout.addWidget(self._open_settings_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self._main_layout.addWidget(self._no_key_widget)

        self.setMinimumSize(500, 480)

    def _apply_styling(self):
        """Apply styling that automatically adapts to light/dark theme via palette()."""
        self.setStyleSheet("""
            QDialog {
                background-color: palette(window);
                color: palette(window-text);
            }
            QTextEdit {
                border: 1px solid palette(mid);
                border-radius: 6px;
                padding: 8px;
                background-color: palette(base);
                color: palette(text);
            }
            QTextEdit:focus {
                border: 1px solid palette(highlight);
            }
            QLabel {
                color: palette(window-text);
                background: transparent;
            }
        """)

        dark = self.palette().color(QPalette.ColorRole.Window).lightness() < 128
        btn_ss = button_stylesheet(dark)
        self._generate_btn.setStyleSheet(btn_ss)
        self._button_box.button(QDialogButtonBox.Ok).setStyleSheet(btn_ss)
        self._button_box.button(QDialogButtonBox.Cancel).setStyleSheet(btn_ss)
        self._open_settings_btn.setStyleSheet(btn_ss)

    def _on_palette_changed(self, palette):
        """Re-apply styling when system light/dark mode changes while dialog is open."""
        self._apply_styling()
        # Force Qt to re-evaluate palette() keywords in stylesheets
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        for widget in self.findChildren(QWidget):
            self.style().unpolish(widget)
            self.style().polish(widget)
            widget.update()

    # -- API key check ----------------------------------------------------

    def _check_ai_availability(self):
        available, message = is_ai_available()
        if not available:
            self._no_key_msg.setText(message)
            self._content.setVisible(False)
            self._no_key_widget.setVisible(True)
            self._generate_btn.setEnabled(False)
            self._status_label.setText("")
        else:
            self._content.setVisible(True)
            self._no_key_widget.setVisible(False)
            self._generate_btn.setEnabled(True)

    # -- Actions ----------------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        self._check_ai_availability()
        QApplication.instance().paletteChanged.connect(self._on_palette_changed)
        self._examples_banner._timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._examples_banner._timer.stop()
        try:
            QApplication.instance().paletteChanged.disconnect(self._on_palette_changed)
        except RuntimeError:
            pass

    def _on_open_settings(self):
        self.open_settings_requested.emit()
        self.reject()

    def _on_generate(self):
        available, message = is_ai_available()
        if not available:
            self._set_status(message, error="warning")
            return

        prompt = self._desc_edit.toPlainText().strip()
        if not prompt:
            self._set_status("Please enter a description.", error=True)
            return

        self._generated_rule = None
        self._preview_edit.setPlainText("")
        self._button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self._generate_btn.setEnabled(False)
        self._generate_btn.setText("Generating…")

        settings = load_settings()
        api_key = settings.get("gemini_api_key", "").strip()
        model = settings.get("gemini_model", list(MODEL_CHOICES.values())[0])

        file_type_rows = list_file_types()
        file_types = [ft["name"] for ft in file_type_rows] if file_type_rows else []

        rule_rows = list_rules()
        existing_names = [r.get("name", "") for r in rule_rows]

        home = os.path.expanduser("~")

        context = {
            "available_file_types": file_types,
            "existing_rule_names": existing_names,
            "username": os.path.basename(home),
            "common_paths": [
                os.path.join(home, "Downloads"),
                os.path.join(home, "Desktop"),
                os.path.join(home, "Documents"),
                os.path.join(home, "Pictures"),
                os.path.join(home, "Movies"),
                os.path.join(home, "Music"),
            ],
        }

        self._last_prompt = prompt
        self._last_context = context
        self._worker = _GenerateRuleWorker(api_key, model, prompt, context, parent=self)
        self._worker.success.connect(self._on_generation_success)
        self._worker.failure.connect(self._on_generation_failure)
        self._worker.finished.connect(self._on_generation_finished)
        self._worker.start()

    def _on_generation_success(self, gemini_rule: dict):
        try:
            app_rule = _convert_gemini_rule_to_app(gemini_rule)
        except Exception as exc:
            self._set_status(f"Conversion error: {exc}", error=True)
            self._generate_btn.setEnabled(True)
            self._generate_btn.setText("Generate Rule")
            return

        self._generated_rule = app_rule
        self._preview_edit.setPlainText(_human_readable_summary(app_rule))
        self._set_status("Rule generated successfully.", error=False)
        self._button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        self._generate_btn.setEnabled(True)
        self._generate_btn.setText("Regenerate")

    def _on_generation_failure(self, message: str):
        display = message if len(message) <= 200 else message[:197] + "…"
        self._set_status(display, error=True)
        self._generate_btn.setEnabled(True)
        self._generate_btn.setText("Generate Rule")

    def _on_generation_finished(self):
        self._generate_btn.setEnabled(True)
        if self._generate_btn.text() == "Generating…":
            self._generate_btn.setText("Generate Rule")
        self._worker = None

    def _on_example_clicked(self, text: str):
        self._desc_edit.setPlainText(text)
        self._desc_edit.setFocus()

    def _on_add_rule(self):
        if self._generated_rule is None:
            return
        self.rule_generated.emit(self._generated_rule)

    # -- Helpers ----------------------------------------------------------

    def _set_status(self, text: str, error: bool | str | None):
        self._status_label.setText(text)
        color = ""
        if error is True:
            color = "color: #d32f2f; background: transparent;"
        elif error == "warning":
            color = "color: #f57c00; background: transparent;"
        elif error is False:
            color = "color: #2e7d32; background: transparent;"
        current = self._status_label.styleSheet()
        if current != color:
            self._status_label.setStyleSheet(color)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = AIRuleDialog()
    dlg.rule_generated.connect(lambda r: print("Rule:", r))
    dlg.show()
    sys.exit(app.exec())
