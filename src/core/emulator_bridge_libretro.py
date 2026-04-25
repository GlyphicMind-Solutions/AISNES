# /AISNES/src/core/emulator_bridge_libretro.py
# AISNES Libretro Emulator Bridge
# Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.



#system imports
import threading, time, pygame
from typing import Any, Dict, Optional

#folder imports
from src.core.snes_wrapper_libretro import SNESWrapperLibretro
from src.adapters.game_context_adapter import GameContextAdapter



# ========================================================================
# EMULATOR BRIDGE LIBRETRO CLASS
# ========================================================================
class EmulatorBridgeLibretro:
    """
    EmulatorBridgeLibretro
    ----------------------
    Bridges the SNES libretro core, AI controllers, and game context adapter.

    Responsibilities:
      - Run the SNES emulator loop
      - Maintain frame timing and stepping
      - Extract world state via GameContextAdapter
      - Call AI controllers (text or vision) on a background thread
      - Apply AI-generated inputs to the emulator

    Notes:
      - mind_p1 and mind_p2 are generic "controller" objects that implement:
            generate_input(state: dict) -> str
      - Vision controllers receive QImage frames in state["frame"]
      - Text controllers receive only structured context and world state
    """

    # ----------------
    # Initialize
    # ----------------
    def __init__(
        self,
        rom_path: str,
        mind_p1: Any,
        mind_p2: Optional[Any] = None,
        *,
        fps: int = 60,
        log=print,
    ):
        self.rom_path = rom_path
        self.mind_p1 = mind_p1
        self.mind_p2 = mind_p2
        self.fps = fps
        self.log = log

        # Emulator wrapper
        self.emu = SNESWrapperLibretro(rom_path=self.rom_path, log=self.log)

        # Audio lock shared with wrapper
        self._audio_lock = threading.Lock()
        self.emu._audio_lock = self._audio_lock

        # Init pygame mixer
        pygame.mixer.init(frequency=self.emu.audio_sample_rate, size=-16, channels=2, buffer=1024)

        # Game context adapter
        self.ctx_adapter = GameContextAdapter()

        # Control flags
        self._running = False
        self._paused = False

        # AI state
        self._ai_thread = None
        self._ai_lock = threading.Lock()
        self._latest_p1_input = "{}"
        self._latest_p2_input = "{}"

# =================================================================== #
# Public control methods                                              #
# =================================================================== #
    # -------------
    # Start
    # -------------
    def start(self):
        if self._running:
            return

        self._running = True
        self._paused = False

        # Start AI thread
        self._ai_thread = threading.Thread(
            target=self._async_ai_loop,
            daemon=True,
        )
        self._ai_thread.start()

        # Start audio thread
        self._audio_thread = threading.Thread(
            target=self._audio_loop,
            daemon=True,
        )
        self._audio_thread.start()

        self.log("[EmulatorBridgeLibretro] Started emulator and AI thread.")

    # ---------
    # Stop
    # ---------
    def stop(self):
        """
        Stop the emulator and AI loop.
        """
        self._running = False
        self._paused = False
        self.log("[EmulatorBridgeLibretro] Stopping emulator...")

    # ---------
    # Pause
    # ---------
    def pause(self):
        """
        Pause the emulator loop (AI thread continues to run on latest state).
        """
        self._paused = True
        self.log("[EmulatorBridgeLibretro] Paused emulator.")

    # ---------
    # Resume
    # ---------
    def resume(self):
        """
        Resume the emulator loop.
        """
        self._paused = False
        self.log("[EmulatorBridgeLibretro] Resumed emulator.")

    # -------------------------
    # Restart ROM
    # -------------------------
    def restart_rom(self):
        """
        Reset emulator and restart AI loop.
        """
        try:
            self.emu.reset()
        except Exception as e:
            self.log(f"[EmulatorBridgeLibretro] Failed to reset ROM: {e}")


# =================================================================== #
# Loops / Logic                                                       #
# =================================================================== #
    # -------------------
    # Audio Loop
    # -------------------
    def _audio_loop(self):
        """
        Simple audio playback loop: pulls PCM from emu buffer and plays via pygame.mixer.
        """
        chunk_size = 2048  # bytes; tune as needed

        while self._running:
            with self._audio_lock:
                if len(self.emu._audio_buffer) >= chunk_size:
                    chunk = self.emu._audio_buffer[:chunk_size]
                    del self.emu._audio_buffer[:chunk_size]
                else:
                    chunk = None

            if chunk:
                snd = pygame.mixer.Sound(buffer=chunk)
                snd.play()
            else:
                time.sleep(0.005)

    # ---------------------------------------------------------
    # Main step loop (called by GUI / main thread)
    # ---------------------------------------------------------
    def step_frame(self):
        """
        Step one frame of the emulator.
        This should be called at ~60 FPS by the main loop or GUI timer.
        """
        if not self._running or self._paused:
            return

        # Apply latest AI inputs
        with self._ai_lock:
            p1_input = self._latest_p1_input
            p2_input = self._latest_p2_input

        self.emu.apply_inputs(p1_input, p2_input)

        # Step the emulator one frame
        self.emu.step_frame()

    # ---------------------------------------------------------
    # AI loop (background thread)
    # ---------------------------------------------------------
    def _async_ai_loop(self):
        """
        Background loop that:
          - Extracts game context
          - Builds world state
          - Calls AI controllers
          - Updates latest inputs
        """
        self.log("[EmulatorBridgeLibretro] AI thread started.")

        target_dt = 1.0 / float(self.fps)

        while self._running:
            start_time = time.time()

            if not self._paused:
                try:
                    self._update_ai()
                except Exception as e:
                    self.log(f"[EmulatorBridgeLibretro] AI update error: {e}")

            elapsed = time.time() - start_time
            sleep_time = max(0.0, target_dt - elapsed)
            time.sleep(sleep_time)

        self.log("[EmulatorBridgeLibretro] AI thread exiting.")

    # ---------------------------------------------------------
    # AI update logic
    # ---------------------------------------------------------
    def _update_ai(self):
        """
        Single AI update step:
          - Extract context from emulator
          - Build world state
          - Call P1/P2 controllers
          - Store latest JSON inputs
        """
        # Extract raw context from emulator
        ctx = self.emu.get_context()

        # Build world state via adapter
        world_state = self.ctx_adapter.build_world_state(ctx)

        # Shared base state for controllers
        base_state: Dict[str, Any] = {
            "ctx": ctx,
            "world": world_state,
        }

        # Player 1
        p1_input = self._run_controller(self.mind_p1, base_state)

        # Player 2 (optional)
        p2_input = "{}"
        if self.mind_p2 is not None:
            p2_input = self._run_controller(self.mind_p2, base_state)

        # Update latest inputs atomically
        with self._ai_lock:
            self._latest_p1_input = p1_input
            self._latest_p2_input = p2_input

# =================================================================== #
# Controller Logic                                                    #
# =================================================================== #
    # ----------------------------------
    # Set Controller
    # ----------------------------------
    def set_controller(self, controller):
        """
        Hot‑swap the AI controller while the emulator is running.
        """
        self.log(f"[EmulatorBridgeLibretro] Swapping controller → {controller}")
        self.mind_p1 = controller
    # ------------------------
    # Run Controller
    # ------------------------
    def _run_controller(self, controller: Any, base_state: Dict[str, Any]) -> str:
        """
        Run a single controller (text or vision) with the given base state.
        If the controller is a vision controller, attach a QImage framebuffer.
        """
        if controller is None:
            return "{}"

        state = dict(base_state)

        # Only attach QImage framebuffer for vision controllers
        controller_type = getattr(controller, "controller_type", None)
        if controller_type == "vision-snes":
            try:
                frame_qimage = self.emu.get_framebuffer_qimage()
                state["frame"] = frame_qimage
            except Exception as e:
                self.log(f"[EmulatorBridgeLibretro] Failed to get QImage framebuffer: {e}")

        try:
            raw = controller.generate_input(state)
            if not isinstance(raw, str):
                raw = "{}"
            return raw
        except Exception as e:
            self.log(f"[EmulatorBridgeLibretro] Controller error ({controller_type}): {e}")
            return "{}"

# =================================================================== #
# Vision Helpers                                                      #
# =================================================================== #
    # --------------------------
    # Get FrameBuffer QImage
    # --------------------------
    def get_framebuffer_qimage(self):
        return self.emu.get_framebuffer_qimage()

