# src/prompts/snes_prompt.py
# AISNES SNES Prompt Builder
# Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.



#system imports
from typing import Any

#local imports
from src.history.history_manager import get_recent_history



# ---------------------
# Build SNES Prompt
# ---------------------
def build_snes_prompt(
    rom_name: str,
    ctx: Any,
    history_limit: int = 5,
) -> str:
    """
    Build a deterministic prompt for SNES controller output.

    Parameters:
      rom_name      - ROM name used to load history
      ctx           - Emulator context object (frame_number, mode, etc.)
      history_limit - Number of recent actions to include

    Returns:
      A formatted prompt string instructing the LLM to output ONLY JSON
      describing SNES button states.
    """

    # Extract context fields
    frame_number = getattr(ctx, "frame_number", 0)
    mode = getattr(ctx, "mode", "unknown")

    # Load recent history from external history manager
    recent = get_recent_history(rom_name, limit=history_limit)

    # Build history block
    history_block = ""
    if recent:
        history_block = "Recent Actions:\n"
        for entry in recent:
            f = entry.get("frame", "?")
            a = entry.get("action", {})
            history_block += f"- Frame {f}: {a}\n"

    # Core instruction block
    instruction_block = (
        "Output ONLY a JSON object describing the next SNES controller state.\n"
        "The JSON object must contain these keys:\n"
        "A, B, X, Y, L, R, START, SELECT, UP, DOWN, LEFT, RIGHT.\n"
        "Each value must be 0 or 1.\n"
        "No explanations. No commentary. JSON only.\n"
    )

    # Context block
    context_block = (
        f"Frame: {frame_number}\n"
        f"Mode: {mode}\n"
    )

    # Final prompt assembly
    prompt = (
        f"{instruction_block}\n"
        f"Game Context:\n{context_block}\n"
        f"{history_block}\n"
        "JSON:"
    )

    return prompt

