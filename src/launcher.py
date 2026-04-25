# /AISNES/src/launcher.py
# AISNES Launcher Utilities
# Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.



#system imports
import json, yaml
from pathlib import Path
from typing import Dict, Any

#folder imports
from src.controllers.llm_controller import LLMController
from src.controllers.text_snes_controller import TextSNESController
from src.controllers.vision_controller import VisionController
from src.core.emulator_bridge_libretro import EmulatorBridgeLibretro
from src.config.ai_config import load_or_create_config
from src.llm.llama_cpp_engine import LlamaCppEngine

#pathing
RECENT_PATH = Path("src/config/recent_roms.json")



# ======================================================= #
# LOADERS SECTION                                         #
# ======================================================= #

# ---------------------------------------------------------
# Load Manifest File
# ---------------------------------------------------------
def load_manifest():
    """
        -Loads the manifest.yaml file with the list of LLM's
    """
    manifest_path = Path("src/models/manifest.yaml")
    if not manifest_path.exists():
        raise FileNotFoundError("manifest.yaml not found")
    return yaml.safe_load(manifest_path.read_text())

# ---------------------------------------------------------
# Load AI configuration (auto-load based on ROM)
# ---------------------------------------------------------
def load_ai_config(rom_path: str) -> Dict[str, Any]:
    """
    Load or create AIConfig for the given ROM.
    AIConfig contains:
      - button map
      - logic sections
      - version
    """
    return load_or_create_config(rom_path)


# ======================================================= #
# BUILDERS SECTION                                        #
# ======================================================= #

# ---------------------------------------------------------
# Build controller from config
# ---------------------------------------------------------
def build_controller(model_name: str, ai_cfg: Dict[str, Any]):
    """
    Build controller using the selected model from manifest.yaml.
    - Resolves model path
    - Loads llama-cpp engine
    - Builds LLMController
    - Returns Text or Vision controller
    """
    models_dir = Path("src/models")

    # 1. Load manifest and verify model exists
    manifest = load_manifest()
    if model_name not in manifest["models"]:
        raise ValueError(f"Model '{model_name}' not found in manifest.yaml")

    info = manifest["models"][model_name]
    model_type = info.get("type", "text")

    # 2. TEMP controller to resolve model path
    temp = LLMController(
        models_dir=models_dir,
        engine=None,
        use_text_model=(model_type == "text"),
        use_vision_model=(model_type == "vision"),
        text_model_key=model_name if model_type == "text" else None,
        vision_model_key=model_name if model_type == "vision" else None,
        log=print,
    )

    # 3. Resolve actual GGUF path
    model_path = temp.text_model_name if model_type == "text" else temp.vision_model_name
    if not model_path:
        raise ValueError(f"Could not resolve model path for key: {model_name}")

    # 4. Create llama.cpp engine
    engine = LlamaCppEngine(
        model_path=model_path,
        n_ctx=4096,
        n_threads=8,
    )

    # 5. Build REAL LLMController with REAL engine
    llm = LLMController(
        models_dir=models_dir,
        engine=engine,
        use_text_model=(model_type == "text"),
        use_vision_model=(model_type == "vision"),
        text_model_key=model_name if model_type == "text" else None,
        vision_model_key=model_name if model_type == "vision" else None,
        log=print,
    )

    # 6. Return correct controller
    if model_type == "vision":
        return VisionController(llm=llm, rom_name=model_name)
    else:
        return TextSNESController(llm=llm, rom_name=model_name)


# ---------------------------------------------------------
# Build emulator + GUI window
# ---------------------------------------------------------
def build_emulator_bridge(rom_path, ai_cfg, preloaded_controller=None):
    """
    Build the emulator bridge and GUI window.
    If a controller was preloaded (model loaded before ROM), use it.
    Otherwise, load the default model.
    """
    if preloaded_controller:
        controller_p1 = preloaded_controller
    else:
        default_model = get_default_model_name()
        controller_p1 = build_controller(default_model, ai_cfg)

    controller_p2 = None  # Optional second controller

    bridge = EmulatorBridgeLibretro(
        rom_path=rom_path,
        mind_p1=controller_p1,
        mind_p2=controller_p2,
        fps=60,
        log=print,
    )

    return {
        "bridge": bridge,
    }


# ======================================================= #
# ROMS SECTION                                            #
# ======================================================= #

# ---------------------------------------------------------
# Load Recent Roms
# ---------------------------------------------------------
def load_recent_roms():
    """
        -Recent Rom Loader
    """
    if RECENT_PATH.exists():
        try:
            return json.loads(RECENT_PATH.read_text())
        except:
            return []
    return []

# ---------------------------------------------------------
# Save Recent Rom
# ---------------------------------------------------------
def save_recent_rom(rom_path: str):
    """
        -Saves Recent Rom
    """
    roms = load_recent_roms()
    if rom_path in roms:
        roms.remove(rom_path)
    roms.insert(0, rom_path)
    roms = roms[:10]  # keep last 10
    RECENT_PATH.write_text(json.dumps(roms, indent=2))


# ======================================================= #
# LLM SECTION                                             #
# ======================================================= #

# ---------------------------------------------------------
# List Available Models
# ---------------------------------------------------------
def list_available_models():
    """
        -Reads manifest.yaml file
        -lists the LLM models available
    """
    manifest_path = Path("src/models/manifest.yaml")

    if not manifest_path.exists():
        return []

    data = yaml.safe_load(manifest_path.read_text())
    return list(data.get("models", {}).keys())

# ---------------------------------------------------------
# Get Default Model Name
# ---------------------------------------------------------
def get_default_model_name():
    """
        -Loads the Default LLM from the manifest.yaml File
    """
    m = load_manifest()
    return m.get("default_text_model")


# ---------------------------------------------------------
# Get Default Text Model
# ---------------------------------------------------------
def get_default_text_model():
    m = load_manifest()
    return m.get("default_text_model")

# ---------------------------------------------------------
# Get Default Vision Model
# ---------------------------------------------------------
def get_default_vision_model():
    m = load_manifest()
    return m.get("default_vision_model")

