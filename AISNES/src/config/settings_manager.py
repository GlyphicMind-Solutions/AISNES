# /AISNES/src/config/settings_manager.py
# AISNES Settings Manager
# Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.



#system imports
import json
from pathlib import Path
from typing import Dict, Any

#pathing
SETTINGS_PATH = Path("src/config/settings.json")



# ---------------------------------------------------------
# Load Settings
# ---------------------------------------------------------
def load_settings() -> Dict[str, Any]:
    """
        -Loads AISNES Settings from settings.json
        -Creates file if missing
    """
    if not SETTINGS_PATH.exists():
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(default_settings(), indent=2))
        return default_settings()

    try:
        return json.loads(SETTINGS_PATH.read_text())
    except Exception:
        return default_settings()

# ---------------------------------------------------------
# Default Settings
# ---------------------------------------------------------
def default_settings() -> Dict[str, Any]:
    """
        -Default AISNES Settings
    """
    return {
        "emulator": {
            "fps_limit": "60",
            "scaling_mode": "Maintain Aspect",
            "frame_skip": "Off"
        },
        "ai": {
            "temperature": 20,
            "max_tokens": 256,
            "history_length": 5,
            "update_rate": 1
        },
        "prompt_logic": {
            "auto_reload_prompt": False,
            "auto_reload_logic": False,
            "save_prompts": False,
            "save_responses": False
        },
        "ui": {
            "theme": "System",
            "font_size": "Medium"
        },
        "gamepad": {
            "mappings": {}
        },
        "advanced": {
            "verbose_logging": False,
            "raw_context": False
        }
    }

# ---------------------------------------------------------
# Save Settings
# ---------------------------------------------------------
def save_settings(settings: Dict[str, Any]):
    """
        -Saves AISNES Settings to settings.json
    """
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2))

# ---------------------------------------------------------
# Save Settings From Dialog
# ---------------------------------------------------------
def save_settings_dialog(dialog):
    """
        -Extracts values from the Settings Dialog
        -Saves them to settings.json
    """
    settings = load_settings()

    # Emulator
    settings["emulator"]["fps_limit"] = dialog.findChild(type(dialog.fps_box), "fps_box").currentText()
    settings["emulator"]["scaling_mode"] = dialog.findChild(type(dialog.scale_box), "scale_box").currentText()
    settings["emulator"]["frame_skip"] = dialog.findChild(type(dialog.skip_box), "skip_box").currentText()

    # AI
    settings["ai"]["temperature"] = dialog.temp_box.value()
    settings["ai"]["max_tokens"] = dialog.max_tokens_box.value()
    settings["ai"]["history_length"] = dialog.history_box.value()
    settings["ai"]["update_rate"] = dialog.update_rate_box.value()

    # Prompt/Logic
    settings["prompt_logic"]["auto_reload_prompt"] = dialog.auto_reload_prompt.isChecked()
    settings["prompt_logic"]["auto_reload_logic"] = dialog.auto_reload_logic.isChecked()
    settings["prompt_logic"]["save_prompts"] = dialog.save_prompts.isChecked()
    settings["prompt_logic"]["save_responses"] = dialog.save_responses.isChecked()

    # UI
    settings["ui"]["theme"] = dialog.theme_box.currentText()
    settings["ui"]["font_size"] = dialog.font_box.currentText()

    # Advanced
    settings["advanced"]["verbose_logging"] = dialog.verbose_log.isChecked()
    settings["advanced"]["raw_context"] = dialog.raw_context.isChecked()

    save_settings(settings)

