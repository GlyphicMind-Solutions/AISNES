# /AISNES/src/controllers/vision_controller.py
# AISNES Vision-Based SNES Controller
# Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.



#system imports
from typing import Any, Dict
from PyQt5.QtGui import QImage

#local imports
from src.prompts.snes_prompt import build_snes_prompt
from src.controllers.llm_controller import LLMController
from src.history.history_manager import append_history


# =========================
# VISION CONTROLLER CLASS
# =========================
class VisionController:
    """
    VisionController
    ----------------
    Uses a multimodal LLM to generate SNES button presses based on:
      - game context
      - world state
      - recent history
      - raw framebuffer image (QImage)

    This controller is model-agnostic and uses LLMController for all LLM calls.
    """

    controller_type = "vision-snes"

    # ---------------------------------------------------------
    # Initialize
    # ---------------------------------------------------------
    def __init__(self, llm: LLMController, rom_name: str):
        self.llm = llm
        self.rom_name = rom_name

    # ---------------------------------------------------------
    # Convert QImage → PNG bytes
    # ---------------------------------------------------------
    def _encode_qimage(self, qimg: QImage) -> bytes:
        """
        Convert a QImage to PNG bytes for multimodal LLM input.
        """
        if qimg is None:
            return b""

        buffer = qimg.bits().asstring(qimg.byteCount())
        width = qimg.width()
        height = qimg.height()
        fmt = qimg.format()

        # Reconstruct QImage to ensure PNG encoding works reliably
        img = QImage(buffer, width, height, fmt)

