# src/history/history_manager.py
# AISNES History Manager
# Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.



#system imports
import json, tempfile, shutil
from pathlib import Path
from datetime import datetime

#pathing
HISTORY_DIR = Path(__file__).parent / "History"
HISTORY_DIR.mkdir(exist_ok=True)



# ---------------------------------------------------------
# Path helper
# ---------------------------------------------------------
def history_path_for_rom(rom_name: str) -> Path:
    stem = Path(rom_name).stem
    return HISTORY_DIR / f"{stem}.json"

# ---------------------------------------------------------
# Safe JSON loader
# ---------------------------------------------------------
def _safe_load_json(path: Path):
    try:
        text = path.read_text()
        return json.loads(text)
    except Exception as e:
        print(f"[History] Load error ({path.name}): {e}")
        print("[History] Attempting auto-repair...")

        try:
            cleaned = text.strip()
            cleaned = cleaned.replace(",}", "}").replace(",]", "]")
            return json.loads(cleaned)
        except Exception:
            print("[History] Auto-repair failed. Resetting history.")
            return []

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
# Load or create history file
# ---------------------------------------------------------
def load_history(rom_name: str):
    path = history_path_for_rom(rom_name)

    if not path.exists():
        return []

    hist = _safe_load_json(path)
    if isinstance(hist, list):
        return hist

    return []

# ---------------------------------------------------------
# Save history (atomic)
# ---------------------------------------------------------
def save_history(rom_name: str, history: list):
    path = history_path_for_rom(rom_name)

    try:
        data = json.dumps(history, indent=2)
    except Exception as e:
        print(f"[History] Refusing to save invalid history for {rom_name}: {e}")
        return

    _atomic_write(path, data)

# ---------------------------------------------------------
# Append a history entry
# ---------------------------------------------------------
def append_history(
    rom_name: str,
    *,
    frame: int,
    action: dict,
    world: dict,
):
    """
    Append a single history entry.

    Parameters:
      frame  - emulator frame number
      action - SNES button JSON (dict)
      world  - world_state from GameContextAdapter
    """

    history = load_history(rom_name)

    entry = {
        "frame": frame,
        "action": action or {},
        "world": world or {},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    history.append(entry)

    # Optional: rolling buffer
    if len(history) > 5000:
        history = history[-1000:]

    save_history(rom_name, history)

# ---------------------------------------------------------
# Get recent history (for prompt builder)
# ---------------------------------------------------------
def get_recent_history(rom_name: str, limit: int = 5):
    history = load_history(rom_name)
    return history[-limit:]

