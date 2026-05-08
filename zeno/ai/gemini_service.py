"""Gemini AI service for generating Zeno rules from natural language."""

import json
import os
from typing import Any, Dict, Optional, Tuple

from zeno.store import load_settings


# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

VALID_FIELDS = {"name", "size", "date", "type"}
VALID_OPERATORS_BY_FIELD = {
    "name": {"matches", "doesn't match"},
    "size": {">=", "<"},
    "date": {">=", "<"},
    "type": {"is", "is not"},
}
VALID_ACTION_TYPES = {"move", "copy", "delete", "trash", "rename", "move_to_subfolder"}
VALID_MATCH_MODES = {"all", "any", "none"}

REQUIRED_TOP_KEYS = {"name", "enabled", "sources", "match_mode", "conditions", "actions"}

def is_ai_available() -> Tuple[bool, str]:
    """
    Returns (is_available, reason_message).
    Checks both the gemini_enabled toggle and API key presence.
    """
    settings = load_settings()
    enabled = settings.get("gemini_enabled", False)
    if not enabled:
        return False, "AI generation is disabled. Enable it in Settings → AI."
    api_key = settings.get("gemini_api_key", "").strip()
    if not api_key:
        return False, "No Gemini API key set. Add your key in Settings → AI."
    return True, ""


MODEL_CHOICES = {
    "Gemini 3.1 Flash-Lite Preview": "gemini-3.1-flash-lite-preview",
    "Gemini 2.5 Flash": "gemini-2.5-flash",
}


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a rule-generation assistant for a macOS file-automation app called Zeno.

Given a user request, return ONLY valid JSON (no markdown fences, no explanation)
matching EXACTLY this structure:

{{
  "name": "Rule name",
  "enabled": true,
  "sources": [
    {{ "path": "/Users/username/Downloads", "recursive": false }}
  ],
  "match_mode": "all",
  "conditions": [
    {{
      "field": "type",
      "operator": "is",
      "value": "Image"
    }}
  ],
  "actions": [
    {{
      "type": "move",
      "target": "/Users/username/Downloads/Images"
    }}
  ]
}}

Rules:
- "field" must be one of: name, size, date, type
- Operators for "name": "matches", "doesn't match"  (value is a glob pattern)
- Operators for "size": ">=", "<"  (value is a string like "100 MB")
- Operators for "date": ">=", "<"  (value is a string like "30 days")
- Operators for "type": "is", "is not"  (value is a file-type name)
- "type" (action) must be one of: move, copy, delete, trash, rename, move_to_subfolder
- For delete/trash actions, omit "target".
- For rename actions, "target" is the name pattern (e.g. "<filename>").
- Use real absolute macOS paths. The current user's home directory is: {home}

Context provided:
- Available file types: {file_types}
- Existing rule names (avoid duplicates): {rule_names}
- Common paths: {paths}

Return ONLY the JSON object. Nothing else.
"""


class GeminiService:
    """Thin wrapper around Google Generative AI for rule generation."""

    def __init__(self, api_key: str, model: str | None = None):
        from google import genai
        if not api_key:
            raise ValueError("A valid Gemini API key is required.")
        self._client = genai.Client(api_key=api_key)
        self._model = model or list(MODEL_CHOICES.values())[0]

    @staticmethod
    def map_gemini_error(exc: Exception) -> str:
        """Map a raw Gemini API exception to a user-friendly string."""
        msg = str(exc)
        msg_lower = msg.lower()

        # 429: Resource Exhausted / Rate Limit
        if "429" in msg or "rate" in msg_lower or "quota" in msg_lower:
            return "Network error: This model is currently experiencing high demand. Please try again later."

        # 500: Internal Server Error
        if "500" in msg or "internal" in msg_lower or "server error" in msg_lower:
            return "Server error: Something went wrong on Google's side. Please try again in a moment."

        # 503: Service Unavailable
        if "503" in msg or "unavailable" in msg_lower:
            return "Service unavailable: Gemini is temporarily unavailable. Please try again later."

        # 401: Unauthenticated
        if "401" in msg or "unauthenticated" in msg_lower or "invalid" in msg_lower:
            return "Auth error: Your API key is invalid or has expired. Please check your settings."

        # 403: Permission Denied
        if "403" in msg or "permission" in msg_lower or "forbidden" in msg_lower:
            return "Permission error: Your API key doesn't have access to this model."

        # 404: Not Found (often model name)
        if "404" in msg or "not found" in msg_lower or "not_found" in msg:
            return "Model error: The selected AI model could not be found. Try a different one in Settings."

        # Connection issues
        if "connection" in msg_lower or "timeout" in msg_lower or "network" in msg_lower:
            return "Network error: Could not reach Gemini. Please check your internet connection."

        # API key related
        if "api key" in msg_lower or "api_key" in msg:
            return "Auth error: Please provide a valid API key in Settings."

        # Generic error - show a friendly message instead of raw error
        return "Connection failed. Please check your API key and try again."

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_rule(self, user_prompt: str, context: dict) -> dict:
        """Send *user_prompt* to Gemini and return a validated rule dict.

        Parameters
        ----------
        user_prompt : str
            Natural-language description of the rule the user wants.
        context : dict
            Must contain ``available_file_types``, ``existing_rule_names``,
            and ``example_paths``.

        Returns
        -------
        dict
            A rule dictionary matching the Zeno schema.

        Raises
        ------
        ValueError
            If Gemini returns invalid JSON or the structure doesn't match.
        """
        home = os.path.expanduser("~")

        system_prompt = _SYSTEM_PROMPT.format(
            home=home,
            file_types=json.dumps(context.get("available_file_types", [])),
            rule_names=json.dumps(context.get("existing_rule_names", [])),
            paths=json.dumps(context.get("example_paths", [
                os.path.join(home, "Downloads"),
                os.path.join(home, "Desktop"),
                os.path.join(home, "Documents"),
            ])),
        )

        from google.genai import types

        response = self._client.models.generate_content(
            model=self._model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
                system_instruction=system_prompt,
            ),
        )

        raw = response.text.strip()

        # Parse JSON
        try:
            rule = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Gemini returned invalid JSON: {exc}\n\nRaw response:\n{raw}"
            ) from exc

        # Validate
        self.validate_rule_schema(rule)
        return rule

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_rule_schema(rule_dict: dict) -> None:
        """Validate that *rule_dict* conforms to the Zeno rule schema.

        Raises ``ValueError`` with a descriptive message on any mismatch.
        """
        if not isinstance(rule_dict, dict):
            raise ValueError("Rule must be a JSON object (dict).")

        missing = REQUIRED_TOP_KEYS - rule_dict.keys()
        if missing:
            raise ValueError(f"Missing required top-level keys: {missing}")

        # -- name --
        if not isinstance(rule_dict["name"], str) or not rule_dict["name"].strip():
            raise ValueError("'name' must be a non-empty string.")

        # -- enabled --
        if not isinstance(rule_dict["enabled"], bool):
            raise ValueError("'enabled' must be a boolean.")

        # -- match_mode --
        if rule_dict["match_mode"] not in VALID_MATCH_MODES:
            raise ValueError(
                f"'match_mode' must be one of {VALID_MATCH_MODES}, "
                f"got '{rule_dict['match_mode']}'."
            )

        # -- sources --
        _validate_sources(rule_dict["sources"])

        # -- conditions --
        _validate_conditions(rule_dict["conditions"])

        # -- actions --
        _validate_actions(rule_dict["actions"])


# ---------------------------------------------------------------------------
# Private validation helpers
# ---------------------------------------------------------------------------

def _validate_sources(sources: Any) -> None:
    if not isinstance(sources, list) or len(sources) == 0:
        raise ValueError("'sources' must be a non-empty list.")
    for i, src in enumerate(sources):
        if not isinstance(src, dict):
            raise ValueError(f"sources[{i}] must be a dict.")
        if "path" not in src:
            raise ValueError(f"sources[{i}] missing 'path'.")
        if not isinstance(src["path"], str) or not src["path"].strip():
            raise ValueError(f"sources[{i}]['path'] must be a non-empty string.")
        if "recursive" in src and not isinstance(src["recursive"], bool):
            raise ValueError(f"sources[{i}]['recursive'] must be a boolean.")


def _validate_conditions(conditions: Any) -> None:
    if not isinstance(conditions, list) or len(conditions) == 0:
        raise ValueError("'conditions' must be a non-empty list.")
    for i, cond in enumerate(conditions):
        if not isinstance(cond, dict):
            raise ValueError(f"conditions[{i}] must be a dict.")
        for key in ("field", "operator", "value"):
            if key not in cond:
                raise ValueError(f"conditions[{i}] missing '{key}'.")

        field = cond["field"]
        if field not in VALID_FIELDS:
            raise ValueError(
                f"conditions[{i}]['field'] must be one of {VALID_FIELDS}, got '{field}'."
            )
        valid_ops = VALID_OPERATORS_BY_FIELD[field]
        if cond["operator"] not in valid_ops:
            raise ValueError(
                f"conditions[{i}]['operator'] for field '{field}' must be one of "
                f"{valid_ops}, got '{cond['operator']}'."
            )


def _validate_actions(actions: Any) -> None:
    if not isinstance(actions, list) or len(actions) == 0:
        raise ValueError("'actions' must be a non-empty list.")
    for i, act in enumerate(actions):
        if not isinstance(act, dict):
            raise ValueError(f"actions[{i}] must be a dict.")
        if "type" not in act:
            raise ValueError(f"actions[{i}] missing 'type'.")
        if act["type"] not in VALID_ACTION_TYPES:
            raise ValueError(
                f"actions[{i}]['type'] must be one of {VALID_ACTION_TYPES}, "
                f"got '{act['type']}'."
            )
        # target is required for everything except delete / trash
        if act["type"] not in ("delete", "trash"):
            if "target" not in act or not isinstance(act.get("target"), str) or not act["target"].strip():
                raise ValueError(
                    f"actions[{i}] of type '{act['type']}' requires a non-empty 'target'."
                )
