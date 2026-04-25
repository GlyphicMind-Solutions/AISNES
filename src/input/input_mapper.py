# /AISNES/src/input/input_mapper.py
# AISNES Input Mapper
# Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.



#system imports
import json
from pathlib import Path
import pygame
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox

#pathing
INPUT_MAP_PATH = Path("src/config/input_map.json")



# ---------------------------------------------------------
# Load Input Map
# ---------------------------------------------------------
def load_input_map():
    """
        -Loads input_map.json
        -Creates file if missing
    """
    if not INPUT_MAP_PATH.exists():
        INPUT_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
        INPUT_MAP_PATH.write_text(json.dumps(default_map(), indent=2))
        return default_map()

    try:
        return json.loads(INPUT_MAP_PATH.read_text())
    except Exception:
        return default_map()

# ---------------------------------------------------------
# Default Mapping
# ---------------------------------------------------------
def default_map():
    """
        -Default SNES button mapping
    """
    return {
        "A": None,
        "B": None,
        "X": None,
        "Y": None,
        "L": None,
        "R": None,
        "START": None,
        "SELECT": None,
        "UP": None,
        "DOWN": None,
        "LEFT": None,
        "RIGHT": None
    }

# ---------------------------------------------------------
# Save Input Map
# ---------------------------------------------------------
def save_input_map(mapping):
    """
        -Saves input_map.json
    """
    INPUT_MAP_PATH.write_text(json.dumps(mapping, indent=2))

# ---------------------------------------------------------
# Open Input Mapper GUI
# ---------------------------------------------------------
def open_input_mapper(parent):
    """
        -Opens a GUI window for assigning gamepad buttons
    """
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        QMessageBox.warning(parent, "Gamepad", "No gamepads detected.")
        return

    js = pygame.joystick.Joystick(0)
    js.init()

    mapping = load_input_map()

    dialog = QDialog(parent)
    dialog.setWindowTitle("Assign Gamepad Buttons")
    dialog.setMinimumSize(400, 300)

    layout = QVBoxLayout()

    label = QLabel("Press a button when prompted.")
    layout.addWidget(label)

    # Assign each SNES button
    for snes_button in mapping.keys():
        btn = QPushButton(f"Assign {snes_button}")
        layout.addWidget(btn)

        # ---------------------------
        # Make Handler
        # ---------------------------
        def make_handler(button_name):
            def handler():
                label.setText(f"Press a button for {button_name}...")
                pygame.event.clear()

                # Wait for button press
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.JOYBUTTONDOWN:
                            mapping[button_name] = f"BUTTON_{event.button}"
                            label.setText(f"{button_name} → BUTTON_{event.button}")
                            waiting = False
                        elif event.type == pygame.JOYHATMOTION:
                            hat = event.value
                            if hat == (0, 1):
                                mapping[button_name] = "HAT_UP"
                            elif hat == (0, -1):
                                mapping[button_name] = "HAT_DOWN"
                            elif hat == (-1, 0):
                                mapping[button_name] = "HAT_LEFT"
                            elif hat == (1, 0):
                                mapping[button_name] = "HAT_RIGHT"
                            label.setText(f"{button_name} → {mapping[button_name]}")
                            waiting = False

            return handler

        btn.clicked.connect(make_handler(snes_button))

    # Save button
    save_btn = QPushButton("Save Mapping")
    save_btn.clicked.connect(lambda: save_input_map(mapping))
    layout.addWidget(save_btn)

    dialog.setLayout(layout)
    dialog.exec_()

