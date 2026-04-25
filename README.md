⭐ AISNES — AI‑Driven SNES Emulator
Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.
AISNES is a modular, open‑source framework that connects a SNES libretro core to local LLMs (text or vision) for real‑time gameplay control.
It is designed for clarity, determinism, and extensibility — with clean separation between emulator, AI logic, world‑state extraction, and GUI.

AISNES does not include any ROMs or copyrighted game assets.

📦 Features
🎮 AI‑Controlled SNES Gameplay
Text‑based LLM controllers

Vision‑based multimodal controllers

Deterministic JSON button‑mask output

External history logging for prompt context

🧠 Modular AI Architecture
Unified LLM controller

Manifest‑based model configuration

Support for text and multimodal models

Clean prompt builder with no persona or identity language

🖼️ Qt‑Based GUI
Real‑time framebuffer display

Smooth 60 FPS rendering

Emulator runs in background thread

🧩 Extensible World‑State Adapter
Converts emulator context into structured world state

Safe for both text and vision models

ROM‑agnostic and easy to extend

🗂️ Clean Project Structure
Controllers

Core emulator bridge

Prompt builder

History manager

GUI

Config system

📁 Project Structure
Code
AISNES/
│
├── README.md
├── main.py
│
└── src/
    ├── controllers/
    │   ├── llm_controller.py
    │   ├── text_snes_controller.py
    │   └── vision_controller.py
    │
    ├── core/
    │   ├── emulator_bridge_libretro.py
    │   └── snes_wrapper_libretro.py
    │
    ├── adapters/
    │   └── game_context_adapter.py
    │
    ├── prompts/
    │   └── snes_prompt.py
    │
    ├── history/
    │   └── history_manager.py
    │
    ├── gui/
    │   └── snes_window.py
    │
    └── config/
        └── ai_config.py
🚀 Getting Started

1. Install Dependencies
AISNES uses:

Python 3.10+

PyQt5 (GUI)

A local LLM engine (e.g., llama.cpp bindings)

A libretro SNES core (not included)

Install Python dependencies:

Code
pip install -r requirements.txt

2. Add Your Models
Place your models and manifest here:

Code
/AISNES/src/models/
    manifest.yaml
    your-models.gguf
Example manifest.yaml:

yaml
default_text_model: text_controller
default_vision_model: vision_controller

models:
  text_controller:
    path: "text-model.gguf"
    type: "text"

  vision_controller:
    path: "vision-model.gguf"
    type: "vision"

3. Run AISNES
Code
python main.py /path/to/your.rom
A Qt window will open and the AI will begin controlling the game.


🧠 How AISNES Works

1. Emulator Bridge
emulator_bridge_libretro.py runs the libretro core, extracts context, and calls AI controllers in a background thread.


2. World State
game_context_adapter.py converts raw emulator context into a structured world dictionary.


3. Prompt Builder
snes_prompt.py builds a deterministic prompt with:

instructions

context

recent history

No identity or persona language is used.


4. AI Controllers
text_snes_controller.py → text‑only LLM

vision_controller.py → multimodal LLM

Each returns JSON button masks only.


5. History Manager
history_manager.py stores recent actions in:

Code
/AISNES/src/history/<rom>.json
This history is used for prompt context.

🛠️ Extending AISNES
You can extend AISNES by:

Adding new world‑state extraction logic

Creating ROM‑specific adapters

Adding new controller types

Integrating different LLM engines

Building custom GUIs

The architecture is intentionally modular and easy to modify.

⚖️ Legal Notice
AISNES does not include:

ROMs

BIOS files

Copyrighted game assets

You must supply your own legally obtained ROMs.

👤 Author
David Kistner (Unconditional Love)
GlyphicMind Solutions LLC
2026

❤️ Contributions
Pull requests are welcome.
AISNES is designed for clarity, modularity, and community‑driven evolution.
