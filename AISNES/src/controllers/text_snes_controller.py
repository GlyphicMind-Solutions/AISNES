# /AISNES/src/controllers/text_snes_controller.py
# AISNES Text-Based SNES Controller
# Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.



#system imports
from typing import Any, Dict

#folder imports
from src.prompts.snes_prompt import build_snes_prompt
from src.controllers.llm_controller import LLMController
from src.history.history_manager import append_history



# ============================
# TEXT SNES CONTROLLER CLASS
# ============================
class TextSNESController:
    """
    TextSNESController
    ------------------
    Uses a text-only LLM to generate SNES button presses based on:
      - game context
      - world state
      - external history
      - deterministic prompt rules

    This controller is model-agnostic and uses LLMController for all LLM calls.
    """

    controller_type = "text-snes"

    # ---------------------------------------------------------
    # Initialize
    # ---------------------------------------------------------
    def __init__(self, llm: LLMController, rom_name: str):
        self.llm = llm
        self.rom_name = rom_name

    # ---------------------------------------------------------
    # Generate Input
    # ---------------------------------------------------------
    def generate_input(self, state: Dict[str, Any]) -> str:
        ctx = state.get("ctx")
        world = state.get("world", {})

        if ctx is None:
            return "{}"

        # Build deterministic SNES prompt
        prompt = build_snes_prompt(
            rom_name=self.rom_name,
            ctx=ctx,
            history_limit=5,
        )

        # Call the LLM through the unified controller
        raw = self.llm.generate_raw_llama(
            prompt=prompt,
            max_tokens=100,
            temperature=0.0,
            top_p=1.0,
            repeat_penalty=1.0,
        )

        # Log history externally
        try:
            append_history(
                self.rom_name,
                frame=ctx.frame_number,
                action={},      # Parsed later by emulator bridge
                world=world,
            )
        except Exception as e:
            print(f"[TextSNESController] Failed to append history: {e}")

        return raw

