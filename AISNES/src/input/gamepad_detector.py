# /AISNES/src/input/gamepad_detector.py
# AISNES Gamepad Detector
# Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.



#system imports
import pygame



# ---------------------------------------------------------
# Detect Gamepads
# ---------------------------------------------------------
def detect_gamepads():
    """
        -Detects connected gamepads using pygame
        -Returns list of device names
    """
    pygame.init()
    pygame.joystick.init()

    pads = []
    count = pygame.joystick.get_count()

    for i in range(count):
        js = pygame.joystick.Joystick(i)
        js.init()
        pads.append(js.get_name())

    return pads

