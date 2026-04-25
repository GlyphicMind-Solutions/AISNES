# /AISNES/ai_config.py
# AI Configuration for AISNES
# Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.



#system imports
import json, tempfile
from pathlib import Path

#pathing
AICONFIG_DIR = Path(__file__).parent / "AIConfig"
AICONFIG_DIR.mkdir(exist_ok=True)



# ---------------------------------------------------------
# Default SNES button map
# ---------------------------------------------------------
def default_buttons():
    return {
        "A": "jump / confirm",
        "B": "run / attack",
        "X": "alt action",
        "Y": "run / attack",
        "L": "shoulder left",
        "R": "shoulder right",
        "START": "pause",
        "SELECT": "menu / select",
        "UP": "move up",
        "DOWN": "move down",
        "LEFT": "move left",
        "RIGHT": "move right",
    }

# ---------------------------------------------------------
# Path helpers
# ---------------------------------------------------------
def _config_path_for_rom(rom_name: str) -> Path:
    stem = Path(rom_name).stem
    return AICONFIG_DIR / f"{stem}.json"

# ---------------------------------------------------------
# Safe JSON loader
# ---------------------------------------------------------
def _safe_load_json(path: Path) -> dict:
    try:
        text = path.read_text()
        return json.loads(text)
    except Exception as e:
        print(f"[AIConfig] Load error ({path.name}): {e}")
        print("[AIConfig] Attempting auto-repair...")

        try:
            cleaned = text.strip()
            cleaned = cleaned.replace(",}", "}").replace(",]", "]")
            return json.loads(cleaned)
        except Exception:
            print("[AIConfig] Auto-repair failed. Resetting config.")
            return None

# ---------------------------------------------------------
# Atomic write helper
# ---------------------------------------------------------
def _atomic_write(path: Path, data: str):
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent)) as f:
            tmp = Path(f.name)
            f.write(data)
        shutil.move(str(tmp), str(path))
    finally:
        if tmp and tmp.exists():
            tmp.unlink(missing_ok=True)

# ---------------------------------------------------------
# Load or create AIConfig (NO HISTORY INSIDE)
# ---------------------------------------------------------
def load_or_create_config(rom_name: str, ask_user_buttons=default_buttons) -> dict:
    path = _config_path_for_rom(rom_name)

    if path.exists():
        cfg = _safe_load_json(path)
        if cfg is not None:
            cfg.setdefault("game", rom_name)
            cfg.setdefault("buttons", ask_user_buttons())
            cfg.setdefault("version", 2)

            # Logic sections (map-based)
            cfg.setdefault("Boot Logic", [])
            cfg.setdefault("Global Logic", [])
            cfg.setdefault("Map Logic", {})

            return cfg

    # Create new config
    buttons = ask_user_buttons()
    cfg = {
        "game": rom_name,
        "buttons": buttons,
        "version": 2,

        # Logic sections
        "Boot Logic": [],
        "Global Logic": [],
        "Map Logic": {},
    }

    _atomic_write(path, json.dumps(cfg, indent=2))
    return cfg

# ---------------------------------------------------------
# Save config (atomic + validated)
# ---------------------------------------------------------
def save_config(rom_name: str, cfg: dict) -> None:
    path = _config_path_for_rom(rom_name)

    try:
        data = json.dumps(cfg, indent=2)
    except Exception as e:
        print(f"[AIConfig] Refusing to save invalid config for {rom_name}: {e}")
        return

    _atomic_write(path, data)

