# /AISNES/src/adapters/game_context_adapter.py
# AISNES Game Context Adapter
# Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.



#system imports
from typing import Any, Dict



# ============================
# GAME CONTEXT ADAPTER CLASS
# ============================
class GameContextAdapter:
    """
    GameContextAdapter
    ------------------
    Converts raw emulator context into structured world state for AI controllers.

    Responsibilities:
      - Interpret emulator context fields (frame number, mode, etc.)
      - Extract any additional metadata needed by AI
      - Provide a stable, deterministic world_state dictionary

    Notes:
      - This adapter intentionally avoids game-specific logic.
      - You can extend this class for specific ROMs or genres.
      - The world_state returned here is safe for both text and vision controllers.
    """

    # -----------
    # Initialize
    # -----------
    def __init__(self):
        pass

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def build_world_state(self, ctx: Any) -> Dict[str, Any]:
        """
        Build a structured world state dictionary from the emulator context.

        Expected ctx fields (provided by SNESWrapperLibretro):
          - frame_number: int
          - mode: str
          - (optional) additional fields depending on emulator implementation

        Returns:
          A dictionary safe for LLM consumption.
        """
        if ctx is None:
            return {
                "frame_number": 0,
                "mode": "unknown",
                "metadata": {},
            }

        # Extract basic fields
        frame_number = getattr(ctx, "frame_number", 0)
        mode = getattr(ctx, "mode", "unknown")

        # Placeholder for future expansion
        metadata = self._extract_metadata(ctx)

        return {
            "frame_number": frame_number,
            "mode": mode,
            "metadata": metadata,
        }

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------
    def _extract_metadata(self, ctx: Any) -> Dict[str, Any]:
        """
        Extract additional metadata from the emulator context.

        This method is intentionally minimal and safe for public release.
        Extend this method to support:
          - WRAM parsing
          - tilemap analysis
          - battle state detection
          - menu detection
          - character stats
          - etc.

        For now, it returns an empty dictionary.
        """
        # TODO: Add game-specific or ROM-specific metadata extraction here.
        return {}

