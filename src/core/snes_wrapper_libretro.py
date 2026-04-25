# /AISNES/src/core/snes_wrapper_libretro.py
# AISNES SNES Libretro Wrapper (Pure CFFI, Corrected)
# Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.


#system imports
import json, struct
import numpy as np
from pathlib import Path
from typing import Optional
from cffi import FFI
from PyQt5.QtGui import QImage


# GLOBAL ACTIVE INSTANCE
ACTIVE_INSTANCE = None

# CFFI SETUP
ffi = FFI()
ffi.cdef("""
typedef short int16_t;
typedef int bool;

typedef void (*retro_video_refresh_t)(const void *data, unsigned width, unsigned height, size_t pitch);
typedef void (*retro_audio_sample_t)(int16_t left, int16_t right);
typedef size_t (*retro_audio_sample_batch_t)(const int16_t *data, size_t frames);
typedef void (*retro_input_poll_t)(void);
typedef int16_t (*retro_input_state_t)(unsigned port, unsigned device, unsigned index, unsigned id);
typedef bool (*retro_environment_t)(unsigned cmd, void *data);
void retro_init(void);
void retro_deinit(void);
unsigned retro_api_version(void);
void retro_get_system_info(struct retro_system_info *info);
void retro_get_system_av_info(struct retro_system_av_info *info);
void retro_set_environment(retro_environment_t);
void retro_set_video_refresh(retro_video_refresh_t);
void retro_set_audio_sample(retro_audio_sample_t);
void retro_set_audio_sample_batch(retro_audio_sample_batch_t);
void retro_set_input_poll(retro_input_poll_t);
void retro_set_input_state(retro_input_state_t);
void retro_reset(void);
void retro_run(void);
bool retro_load_game(const struct retro_game_info *game);
void retro_unload_game(void);
size_t retro_serialize_size(void);
bool retro_serialize(void *data, size_t size);
bool retro_unserialize(const void *data, size_t size);

struct retro_game_info {
    const char *path;
    const void *data;
    size_t size;
    const char *meta;
};

struct retro_system_info {
    const char *library_name;
    const char *library_version;
    const char *valid_extensions;
    bool need_fullpath;
    bool block_extract;
};

struct retro_system_av_info {
    struct retro_game_geometry {
        unsigned base_width;
        unsigned base_height;
        unsigned max_width;
        unsigned max_height;
        float aspect_ratio;
    } geometry;

    struct retro_system_timing {
        double fps;
        double sample_rate;
    } timing;
};

""")

# Load SNES9x core
CORE_PATH = "emu/libretro_snes9x.so"
lib = ffi.dlopen(CORE_PATH)


# --------------------------------
# MODULE‑LEVEL CALLBACKS
# --------------------------------
@ffi.callback("void(const void*, unsigned, unsigned, size_t)")
def video_refresh_cb(data, width, height, pitch):
    if ACTIVE_INSTANCE:
        ACTIVE_INSTANCE.video_refresh_impl(data, width, height, pitch)

@ffi.callback("void(int16_t, int16_t)")
def audio_sample_cb(left, right):
    if ACTIVE_INSTANCE:
        ACTIVE_INSTANCE.audio_sample_impl(left, right)

@ffi.callback("size_t(const int16_t*, size_t)")
def audio_sample_batch_cb(data, frames):
    if ACTIVE_INSTANCE:
        return ACTIVE_INSTANCE.audio_sample_batch_impl(data, frames)
    return frames

@ffi.callback("void()")
def input_poll_cb():
    if ACTIVE_INSTANCE:
        ACTIVE_INSTANCE.input_poll_impl()

@ffi.callback("int16_t(unsigned, unsigned, unsigned, unsigned)")
def input_state_cb(port, device, index, id_):
    if ACTIVE_INSTANCE:
        return ACTIVE_INSTANCE.input_state_impl(port, device, index, id_)
    return 0

@ffi.callback("bool(unsigned, void*)")
def environment_cb(cmd, data):
    # RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY = 9
    if cmd == 9:
        p = ffi.cast("const char **", data)
        p[0] = ffi.NULL
        return True

    # RETRO_ENVIRONMENT_SET_PIXEL_FORMAT = 10
    if cmd == 10:
        fmt = ffi.cast("const int *", data)[0]
        if ACTIVE_INSTANCE:
            ACTIVE_INSTANCE.pixel_format = fmt
            ACTIVE_INSTANCE.log(f"[SNESWrapperLibretro] Pixel format set to {fmt}")
        return True

    return False



# ================================
# SIMPLE CONTEXT CLASS
# ================================
class SimpleContext:
    # --------------
    # Initialize 
    # --------------
    def __init__(self, frame_number, width, height, frame):
        """
            -Sets Frame Number, width, height of the Emulator
        """
        self.frame_number = frame_number
        self.width = width
        self.height = height
        self.frame = frame



# ================================
# SNES WRAPPER CLASS
# ================================
class SNESWrapperLibretro:
    """
    Pure CFFI SNES9x Wrapper
    ------------------------
    - Loads SNES9x core directly
    - Registers callbacks
    - Handles RGB565 → RGB888
    - Produces numpy frames
    - Integrates with AISNES GUI + AI
    """
    # --------------
    # Initialize 
    # --------------
    def __init__(self, rom_path: str, log=print):
        """
            -Initialize SNES Wrapper Libretro Class
                --sets active/global instances
                --sets framebuffer and input state
        """
        global ACTIVE_INSTANCE
        ACTIVE_INSTANCE = self

        #pathing/log
        self.rom_path = rom_path
        self.log = log

        # framebuffer
        self.frame = None
        self.fb_width = 0
        self.fb_height = 0
        self.frame_number = 0
        self.pixel_format = 2  # assume RGB565 unless told otherwise
        self._max_framebuffer_size = 512 * 224 * 4
        self._framebuffer_storage = bytearray(self._max_framebuffer_size)
        self._fb_pitch = 0

        # audio
        self.audio_sample_rate = 32000  # SNES9x default; can be overridden later
        self._audio_buffer = bytearray()
        self._audio_lock = None  # will be set by bridge or global

        # input state
        self.input_state = {}

        # initialize emulator
        self._init_emulator()

    # ---------------------------------------------------------
    # Emulator Initialization
    # ---------------------------------------------------------
    def _init_emulator(self):
        """
            -Initializes Emulator with callbacks and rom loading
        """
        self.log(f"[SNESWrapperLibretro] Initializing emulator with {self.rom_path}")

        # Register callbacks
        lib.retro_set_video_refresh(video_refresh_cb)
        lib.retro_set_audio_sample(audio_sample_cb)
        lib.retro_set_audio_sample_batch(audio_sample_batch_cb)
        lib.retro_set_input_poll(input_poll_cb)
        lib.retro_set_input_state(input_state_cb)
        lib.retro_set_environment(environment_cb)

        self.log("[SNESWrapperLibretro] Calling retro_init()")
        lib.retro_init()

        # Load ROM
        rom_path = Path(self.rom_path)
        if not rom_path.exists():
            raise FileNotFoundError(f"ROM not found: {rom_path}")

        with open(rom_path, "rb") as f:
            data = f.read()

        # keep ROM buffer alive on self so C doesn't point to freed memory
        self._rom_buf = ffi.new("char[]", data)

        game_info = ffi.new("struct retro_game_info *")
        game_info.path = ffi.new("char[]", str(rom_path).encode("utf-8"))
        game_info.data = self._rom_buf
        game_info.size = len(data)
        game_info.meta = ffi.NULL

        self.log("[SNESWrapperLibretro] Calling retro_load_game()")
        if not lib.retro_load_game(game_info):
            raise RuntimeError("Failed to load SNES9x core with ROM")

# =========================================================== #
# INSTANCE CALLBACK IMPLEMENTATIONS                           #
# =========================================================== #
    # ------------------------------
    # Video Refresh Implementation
    # ------------------------------
    def video_refresh_impl(self, data, width, height, pitch):
        if data == ffi.NULL or width == 0 or height == 0:
            return

        size = height * pitch
        if size == 0 or size > self._max_framebuffer_size:
            return

        # Deep copy into persistent storage
        raw = bytes(ffi.buffer(data, size))
        self._framebuffer_storage[:size] = raw

        self.fb_width = width
        self.fb_height = height
        self._fb_pitch = pitch
        self.frame_number += 1

    # -----------------------------
    # Audio Sample Implementation
    # -----------------------------
    def audio_sample_impl(self, left, right):
        # 16-bit signed little-endian stereo: L, R
        if self._audio_lock is None:
            return
        with self._audio_lock:
            self._audio_buffer += struct.pack("<hh", left, right)

    # -----------------------------------
    # Audio Sample Batch Implementation
    # -----------------------------------
    def audio_sample_batch_impl(self, data, frames):
        if self._audio_lock is None:
            return frames
        # data is int16_t* interleaved stereo: L R L R ...
        buf = ffi.buffer(data, frames * 2 * 2)  # frames * channels * bytes_per_sample
        with self._audio_lock:
            self._audio_buffer += buf[:]
        return frames

    # ---------------------------
    # Input Poll Implementation
    # ---------------------------
    def input_poll_impl(self):
        pass

    # ----------------------------
    # Input State Implementation
    # ----------------------------
    def input_state_impl(self, port, device, index, id_):
        return 1 if self.input_state.get(id_, False) else 0

    # ----------------------------
    # Environment Implementation
    # ----------------------------
    def environment_impl(self, cmd, data):
        return False

# =========================================================== #
# Input Handling                                              #
# =========================================================== #
    # ---------------------
    # Apply Inputs
    # ---------------------
    def apply_inputs(self, p1_json: str, p2_json: str):
        """
            -Apply Inputs from LLM
                --LLM output becomes button mapped
        """
        try:
            p1 = json.loads(p1_json) if p1_json else {}
        except:
            p1 = {}

        mapping = {
            "B": 0, "Y": 1, "SELECT": 2, "START": 3,
            "UP": 4, "DOWN": 5, "LEFT": 6, "RIGHT": 7,
            "A": 8, "X": 9, "L": 10, "R": 11,
        }

        self.input_state = {mapping[k]: bool(v) for k, v in p1.items() if k in mapping}

    # -------------------
    # Get Context
    # -------------------
    def get_context(self):
        return SimpleContext(
            frame_number=self.frame_number,
            width=self.fb_width,
            height=self.fb_height,
            frame=self.frame
        )


# =========================================================== #
# Frame Section                                               #
# =========================================================== #
    # --------------
    # Step Frame
    # --------------
    def step_frame(self):
        lib.retro_run()
        self.frame_number += 1

    # ----------------
    # Get Frame Numpy
    # ----------------
    def get_frame_numpy(self):
        return self.frame

    # ------------------------
    # Get Framebuffer QImage
    # ------------------------
    def get_framebuffer_qimage(self):
        if self.fb_width == 0 or self.fb_height == 0:
            return None

        w, h, pitch = self.fb_width, self.fb_height, self._fb_pitch
        fmt = self.pixel_format
        src = self._framebuffer_storage

        if fmt == 1:  # XRGB8888
            img = QImage(src, w, h, pitch, QImage.Format_RGB32)
            return img.copy()

        if fmt == 2:  # RGB565
            img = QImage(src, w, h, pitch, QImage.Format_RGB16)
            return img.copy()

        if fmt == 0:  # 0RGB1555 fallback
            img = QImage(src, w, h, pitch, QImage.Format_RGB16)
            return img.copy()

        return None

# =========================================================== #
# Game States                                                 #
# =========================================================== #
    # --------------
    # Save State 
    # --------------
    def save_state(self, path: str):
        size = lib.retro_serialize_size()
        buf = ffi.new(f"char[{size}]")
        if lib.retro_serialize(buf, size):
            with open(path, "wb") as f:
                f.write(ffi.buffer(buf, size))

    # --------------
    # Load State
    # --------------
    def load_state(self, path: str):
        with open(path, "rb") as f:
            data = f.read()
        buf = ffi.new(f"char[{len(data)}]", data)
        return lib.retro_unserialize(buf, len(data))

    # --------------
    # Reset
    # --------------
    def reset(self):
        lib.retro_reset()
        self.frame_number = 0

