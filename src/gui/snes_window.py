# /AISNES/src/gui/snes_window.py
# AISNES SNES GUI Window
# Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.



#system imports
import json
from pathlib import Path
from typing import Optional
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QFileDialog,
    QMainWindow, QAction, QMenuBar, QMessageBox,
    QDockWidget, QTextEdit, QInputDialog, QDialog,
    QTabWidget, QFormLayout, QSpinBox, QComboBox,
    QCheckBox, QPushButton, QHBoxLayout
)

#folder imports
from src.input.gamepad_detector import detect_gamepads
from src.input.input_mapper import open_input_mapper
from src.history.history_manager import get_recent_history
from src.prompts.snes_prompt import build_snes_prompt
from src.config.settings_manager import save_settings_dialog
from src.launcher import (
    load_ai_config,
    build_controller,
    build_emulator_bridge,
    load_recent_roms,
    save_recent_rom,
    list_available_models,
)


# ========================================================
# SNES WINDOW CLASS
# ========================================================
class SNESWindow(QMainWindow):
    """
    SNESWindow
    ----------
    Qt-based GUI window for displaying the SNES framebuffer.

    Responsibilities:
      - Display the emulator framebuffer at ~60 FPS
      - Provide a full menu bar:
          - Open ROM
          - Restart ROM
          - Save/Load State
          - Recent ROMs
          - Load LLM Model
          - Exit
      - Provide Debug Tools:
          - World State Viewer
          - Prompt Viewer
          - Action History Viewer
      - Provide Editor Tools:
          - Prompt Template Editor
          - Logic JSON Editor
    """

    # --------------
    # Initialize
    # --------------
    def __init__(self, *, fps: int = 60, title: str = "AISNES Emulator"):
        """
            -Initializes the GUI
            -Builds the Menu Bar
            -Builds Debug Panels
            -Builds Editor Panels
            -Prompts user for Rom before loading emulator
            -Sets FPS
        """
        super().__init__()

        self.bridge = None
        self.fps = fps
        self.current_rom_path = None

        # Window title/size
        self.setWindowTitle(title)
        self.setMinimumSize(256 * 2, 224 * 2)

        # Central widget
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Status bar indicator
        self.status_label = QLabel("Mode: No ROM Loaded")
        self.statusBar().addPermanentWidget(self.status_label)

        # Build panels and Menu
        self._build_debug_panels()
        self._build_editor_panels()
        self._build_menu_bar()

        #debug log
        self.debug_log = []

        #selected controller
        self.selected_controller = None

# =========================================================== #
# Helpers Section                                             #
# =========================================================== #
    # ----------------------
    # Debug
    # ----------------------
    def _debug(self, msg: str):
        """
            -Sets Debug Log
        """
        self.debug_log.append(msg)
        if len(self.debug_log) > 2000:
            self.debug_log.pop(0)
 
    # ----------------------
    # Get Debug Log
    # ----------------------
    def get_debug_log(self):
        return "\n".join(self.debug_log)


# =========================================================== #
# Menu Section                                                #
# =========================================================== #
    # ---------------------------------------------------------
    # Menu Bar
    # ---------------------------------------------------------
    def _build_menu_bar(self):
        """
            -Builds the Menu Bar for the GUI Window:
                --/File Menu/
                    - Open Rom 
                    - Restart Rom 
                    - Save State
                    - Load State
                    - Recent Roms
                    - Exit
                --/LLMs Menu/
                    - Load Model
                --/Debug Menu/
                    - World State
                    - Prompt
                    - Action History
                --/Editor Menu/
                    - Edit Prompt Template
                    - Edit Logic JSON
                --/Settings/
                    - Open Settings
                --/AI/
                    -Assign LLM Controller
                    -LLM Chat

        """
        menubar = self.menuBar()

        #--- FILE MENU ---#
        file_menu = menubar.addMenu("File")
        #open rom
        open_action = QAction("Open ROM", self)
        open_action.triggered.connect(self._open_rom)
        file_menu.addAction(open_action)
        #restart rom
        restart_action = QAction("Restart ROM", self)
        restart_action.triggered.connect(self._restart_rom)
        file_menu.addAction(restart_action)
        #save state
        save_state_action = QAction("Save State", self)
        save_state_action.triggered.connect(self._save_state)
        file_menu.addAction(save_state_action)
        #load state
        load_state_action = QAction("Load State", self)
        load_state_action.triggered.connect(self._load_state)
        file_menu.addAction(load_state_action)
        #-Recent ROMs submenu-
        recent_menu = file_menu.addMenu("Recent ROMs")
        self.recent_menu = recent_menu
        self._refresh_recent_roms()
        file_menu.addSeparator()
        #exit
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        #--- LLMs MENU ---#
        model_menu = menubar.addMenu("LLMs")
        #load model
        load_model_action = QAction("Load Model", self)
        load_model_action.triggered.connect(self._load_llm_model)
        model_menu.addAction(load_model_action)

        #--- DEBUG MENU ---#
        debug_menu = menubar.addMenu("Debug")
        #llm debug
        llm_debug_action = QAction("LLM Debug", self)
        llm_debug_action.triggered.connect(lambda: self.llm_debug_dock.setVisible(True))
        debug_menu.addAction(llm_debug_action)
        #world state
        world_action = QAction("World State", self)
        world_action.triggered.connect(lambda: self.world_dock.setVisible(True))
        debug_menu.addAction(world_action)
        #prompt
        prompt_action = QAction("Prompt", self)
        prompt_action.triggered.connect(lambda: self.prompt_dock.setVisible(True))
        debug_menu.addAction(prompt_action)
        #action history
        history_action = QAction("Action History", self)
        history_action.triggered.connect(lambda: self.history_dock.setVisible(True))
        debug_menu.addAction(history_action)

        #--- EDITOR MENU ---#
        editor_menu = menubar.addMenu("Editor")
        #edit prompt template
        edit_prompt_action = QAction("Edit Prompt Template", self)
        edit_prompt_action.triggered.connect(self._open_prompt_editor)
        editor_menu.addAction(edit_prompt_action)
        #edit logic json
        edit_logic_action = QAction("Edit Logic JSON", self)
        edit_logic_action.triggered.connect(self._open_logic_editor)
        editor_menu.addAction(edit_logic_action)

        #--- SETTINGS MENU ---#
        settings_menu = menubar.addMenu("Settings")
        #open settings
        open_settings_action = QAction("Open Settings", self)
        open_settings_action.triggered.connect(self._open_settings_menu)
        settings_menu.addAction(open_settings_action)

        # --- AI MENU ---#
        ai_menu = menubar.addMenu("AI")
        #Assign AI to Player 1
        assign_p1 = QAction("Assign AI as Player 1", self)
        assign_p1.triggered.connect(self._assign_ai_to_p1)
        ai_menu.addAction(assign_p1)
        #Assign AI to Player 2
        assign_p2 = QAction("Assign AI as Player 2", self)
        assign_p2.triggered.connect(self._assign_ai_to_p2)
        ai_menu.addAction(assign_p2)
        #Remove AI from Player 1
        remove_p1 = QAction("Remove AI from Player 1", self)
        remove_p1.triggered.connect(self._remove_ai_from_p1)
        ai_menu.addAction(remove_p1)
        #Remove AI from Player 2
        remove_p2 = QAction("Remove AI from Player 2", self)
        remove_p2.triggered.connect(self._remove_ai_from_p2)
        ai_menu.addAction(remove_p2)
        ai_menu.addSeparator()
        #AI Chat
        chat_action = QAction("AI Chat", self)
        chat_action.setCheckable(True)
        chat_action.triggered.connect(lambda checked: self.chat_dock.setVisible(checked))
        self.chat_dock.visibilityChanged.connect(chat_action.setChecked)
        ai_menu.addAction(chat_action)


# =========================================================== #
# Panels Section                                              #
# =========================================================== #
    # ---------------------------------------------------------
    # Debug Panels
    # ---------------------------------------------------------
    def _build_debug_panels(self):
        """
            -Builds the Debug Panels:
                -World State Viewer
                -Prompt Viewer
                -Action History Viewer
                -LLM Debug
                -LLM Chat
        """

        #--- WORLD STATE PANEL ---#
        self.world_text = QTextEdit()
        self.world_text.setReadOnly(True)
        #World State Dock
        self.world_dock = QDockWidget("World State", self)
        self.world_dock.setWidget(self.world_text)
        self.addDockWidget(Qt.RightDockWidgetArea, self.world_dock)
        self.world_dock.hide()

        #--- PROMPT PANEL ---#
        self.prompt_text = QTextEdit()
        self.prompt_text.setReadOnly(True)
        #Prompt Dock
        self.prompt_dock = QDockWidget("Prompt", self)
        self.prompt_dock.setWidget(self.prompt_text)
        self.addDockWidget(Qt.RightDockWidgetArea, self.prompt_dock)
        self.prompt_dock.hide()

        #--- ACTION HISTORY PANEL ---#
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        #Action History Dock
        self.history_dock = QDockWidget("Action History", self)
        self.history_dock.setWidget(self.history_text)
        self.addDockWidget(Qt.RightDockWidgetArea, self.history_dock)
        self.history_dock.hide()

        # --- LLM DEBUG PANEL ---#
        self.llm_debug_text = QTextEdit()
        self.llm_debug_text.setReadOnly(True)
        #LLM Debug Dock
        self.llm_debug_dock = QDockWidget("LLM Debug", self)
        self.llm_debug_dock.setWidget(self.llm_debug_text)
        self.addDockWidget(Qt.RightDockWidgetArea, self.llm_debug_dock)
        self.llm_debug_dock.hide()

        # --- LLM CHAT PANEL ---#
        #history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        #input window layout
        self.chat_input = QTextEdit()
        self.chat_input.setFixedHeight(60)
        #send button
        self.chat_send_btn = QPushButton("Send")
        self.chat_send_btn.clicked.connect(self._send_chat_message)
        #chat container
        chat_container = QWidget()
        chat_layout = QVBoxLayout()
        chat_layout.addWidget(self.chat_history)
        chat_layout.addWidget(self.chat_input)
        chat_layout.addWidget(self.chat_send_btn)
        chat_container.setLayout(chat_layout)
        #LLM Chat Dock
        self.chat_dock = QDockWidget("LLM Chat", self)
        self.chat_dock.setWidget(chat_container)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.chat_dock)
        self.chat_dock.hide()

    # ---------------------------------------------------------
    # Editor Panels
    # ---------------------------------------------------------
    def _build_editor_panels(self):
        """
            -Builds the Editor Panels:
                -Prompt Template Editor
                -Logic JSON Editor
        """

        #--- PROMPT TEMPLATE EDITOR PANEL ---#
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setReadOnly(False)
        #Prompt Template Editor
        self.prompt_edit_dock = QDockWidget("Prompt Template Editor", self)
        self.prompt_edit_dock.setWidget(self.prompt_edit)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.prompt_edit_dock)
        self.prompt_edit_dock.hide()

        #--- LOGIC JSON EDITOR PANEL ---#
        self.logic_edit = QTextEdit()
        self.logic_edit.setReadOnly(False)
        #Logic JSON editor
        self.logic_edit_dock = QDockWidget("Logic JSON Editor", self)
        self.logic_edit_dock.setWidget(self.logic_edit)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.logic_edit_dock)
        self.logic_edit_dock.hide()


# =========================================================== #
# Editors Section                                             #
# =========================================================== #
    # ---------------------------------------------------------
    # Prompt Template Editor
    # ---------------------------------------------------------
    def _open_prompt_editor(self):
        """
            -Opens the Prompt Template Editor for the current ROM
        """
        if not self.current_rom_path:
            QMessageBox.warning(self, "Prompt Editor", "No ROM loaded.")
            return

        rom_name = Path(self.current_rom_path).stem
        template_path = Path(f"src/prompts/templates/{rom_name}.txt")

        if not template_path.exists():
            template_path.parent.mkdir(parents=True, exist_ok=True)
            template_path.write_text("")

        text = template_path.read_text()
        self.prompt_edit.setText(text)
        self.prompt_edit_dock.show()

        # Save on close
        def save_template():
            template_path.write_text(self.prompt_edit.toPlainText())

        self.prompt_edit_dock.visibilityChanged.connect(
            lambda visible: save_template() if not visible else None
        )

    # ---------------------------------------------------------
    # Logic JSON Editor
    # ---------------------------------------------------------
    def _open_logic_editor(self):
        """
            -Opens the Logic JSON Editor for the current ROM
        """
        if not self.current_rom_path:
            QMessageBox.warning(self, "Logic Editor", "No ROM loaded.")
            return

        ai_cfg_path = Path(f"src/config/AIConfig/{Path(self.current_rom_path).stem}.json")

        if not ai_cfg_path.exists():
            QMessageBox.warning(self, "Logic Editor", "AIConfig JSON not found.")
            return

        text = ai_cfg_path.read_text()
        self.logic_edit.setText(text)
        self.logic_edit_dock.show()

        # Save on close
        def save_logic():
            ai_cfg_path.write_text(self.logic_edit.toPlainText())

        self.logic_edit_dock.visibilityChanged.connect(
            lambda visible: save_logic() if not visible else None
        )

# =========================================================== #
# ROMs Section                                                #
# =========================================================== #
    # ---------------------------------------------------------
    # ROM Loading
    # ---------------------------------------------------------
    def _open_rom(self, initial=False):
        """
            -Rom Loader
        """

        if not initial:
            rom_path, _ = QFileDialog.getOpenFileName(
                self, "Select SNES ROM", "", "SNES ROMs (*.smc *.sfc *.fig *.bin *.rom)"
            )
            if not rom_path:
                return
        else:
            rom_path, _ = QFileDialog.getOpenFileName(
                self, "Select SNES ROM", "", "SNES ROMs (*.smc *.sfc *.fig *.bin *.rom)"
            )
            if not rom_path:
                self.close()
                return

        self.current_rom_path = rom_path
        save_recent_rom(rom_path)

        ai_cfg = load_ai_config(rom_path)
        result = build_emulator_bridge(
            rom_path,
            ai_cfg,
            preloaded_controller=None
        )
        self.bridge = result["bridge"]

        # Timer for GUI updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_frame)
        self.timer.start(int(1000 / self.fps))

        self.bridge.start()
        self._refresh_recent_roms()
        self._update_status_bar()

    # ---------------------------------------------------------
    # Refresh Recent ROMs List
    # ---------------------------------------------------------
    def _refresh_recent_roms(self):
        """
            -Refreshes the recent Roms List
        """
        self.recent_menu.clear()
        roms = load_recent_roms()
        for rom in roms:
            action = QAction(rom, self)
            action.triggered.connect(lambda _, r=rom: self._open_recent(r))
            self.recent_menu.addAction(action)

    # ---------------------------------------------------------
    # Open Recent Rom
    # ---------------------------------------------------------
    def _open_recent(self, rom_path):
        """
            -Opens recent rom
        """
        ai_cfg = load_ai_config(rom_path)
        result = build_emulator_bridge(
            rom_path,
            ai_cfg,
            preloaded_controller=None
        )
        self.bridge = result["bridge"]
        self.bridge.start()
        self._update_status_bar()

    # ---------------------------------------------------------
    # Restart ROM
    # ---------------------------------------------------------
    def _restart_rom(self):
        """
            -Restarts the Rom
        """
        if self.bridge:
            self.bridge.restart_rom()
            self._update_status_bar()


# =========================================================== #
# Game States Section                                         #
# =========================================================== #
    # ---------------------------------------------------------
    # Save State
    # ---------------------------------------------------------
    def _save_state(self):
        """
            -Saves the current Rom State
        """
        if not self.bridge:
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save State", "", "State Files (*.state)")
        if path:
            self.bridge.emu.save_state(path)

    # ---------------------------------------------------------
    # Load State
    # ---------------------------------------------------------
    def _load_state(self):
        """
            -Loads a Rom State
        """
        if not self.bridge:
            return

        path, _ = QFileDialog.getOpenFileName(self, "Load State", "", "State Files (*.state)")
        if path:
            self.bridge.emu.load_state(path)


# =========================================================== #
# Function Updates for GUI                                    #
# =========================================================== #
    # -------------------
    # Update Status Bar
    # -------------------
    def _update_status_bar(self):
        """
            -Updater for the Status Bar
                -indicates rom state, player status, model loaded, and AI status
        """

        if not self.bridge:
            self.status_label.setText("Mode: No ROM Loaded")
            return

        p1 = "AI" if self.bridge.mind_p1 else "Human"
        p2 = "AI" if self.bridge.mind_p2 else "Human"
        self.status_label.setText(f"Mode: P1={p1} | P2={p2}")

        model = self.selected_model_name if self.selected_controller else "None"
        self.status_label.setText(f"Mode: P1={p1} | P2={p2} | Model={model}")

    # ---------------------------------------------------------
    # Frame update
    # ---------------------------------------------------------
    def _update_frame(self):
        """
            -Updates the current frame
        """
        if not self.bridge:
            return

        try:
            self.bridge.step_frame()
            qimg: QImage = self.bridge.get_framebuffer_qimage()
            if qimg:
                pix = QPixmap.fromImage(qimg)
                self.label.setPixmap(pix.scaled(
                    self.label.width(),
                    self.label.height(),
                    Qt.KeepAspectRatio,
                    Qt.FastTransformation,
                ))

            # Update debug panels
            self._update_debug_panels()

        except Exception as e:
            print(f"[SNESWindow] Frame update error: {e}")

    # ---------------------------------------------------------
    # Debug Panel Updates
    # ---------------------------------------------------------
    def _update_debug_panels(self):
        """
            -Updates World State, Prompt, and Action History Panels
        """
        if not self.bridge:
            return

        # LLM DEBUG
        if self.llm_debug_dock.isVisible():
            try:
                log = self.bridge.mind_p1.llm.get_debug_log()
                self.llm_debug_text.setText(log)
            except Exception as e:
                self.llm_debug_text.setText(f"[LLM DEBUG ERROR] {e}")

        # WORLD STATE
        if self.world_dock.isVisible():
            ctx = self.bridge.emu.get_context()
            world = self.bridge.ctx_adapter.build_world_state(ctx)
            self.world_text.setText(json.dumps(world, indent=2))

        # PROMPT
        if self.prompt_dock.isVisible():
            ctx = self.bridge.emu.get_context()
            prompt = build_snes_prompt(
                rom_name=self.bridge.rom_path,
                ctx=ctx,
                history_limit=5,
            )
            self.prompt_text.setText(prompt)

        # ACTION HISTORY
        if self.history_dock.isVisible():
            hist = get_recent_history(self.bridge.rom_path, limit=20)
            self.history_text.setText(json.dumps(hist, indent=2))


# =========================================================== #
# SETTINGS                                                    #
# =========================================================== #
    # ---------------------------------------------------------
    # Settings Menu
    # ---------------------------------------------------------
    def _open_settings_menu(self):
        """
            -Opens the AISNES Settings Menu
        """
        self._build_settings_dialog()
        self.settings_dialog.show()

    # ---------------------------------------------------------
    # Settings Dialog Builder
    # ---------------------------------------------------------
    def _build_settings_dialog(self):
        """
            -Builds the AISNES Settings Dialog:
                -Emulator Settings
                -AI Settings
                -Prompt/Logic Behavior
                -UI Settings
                -Gamepad Settings
                -Advanced Settings
        """
        ##--- SETTINGS DIALOG WINDOW ---##

        #set window title/size
        self.settings_dialog = QDialog(self)
        self.settings_dialog.setWindowTitle("AISNES Settings")
        self.settings_dialog.setMinimumSize(500, 400)
        #tabs/layout
        tabs = QTabWidget()
        layout = QVBoxLayout()
        layout.addWidget(tabs)

        #--- Emulator Settings Tab ---#
        emulator_tab = QWidget()
        emulator_layout = QFormLayout()
        # FPS Limit
        self.settings_dialog.fps_box = QComboBox()
        self.settings_dialog.fps_box.setObjectName("fps_box")
        self.settings_dialog.fps_box.addItems(["30", "60", "Unlimited"])
        emulator_layout.addRow("FPS Limit:", self.settings_dialog.fps_box)
        # Scaling Mode
        self.settings_dialog.scale_box = QComboBox()
        self.settings_dialog.scale_box.setObjectName("scale_box")
        self.settings_dialog.scale_box.addItems(
            ["Pixel-Perfect", "2x", "3x", "4x", "Stretch", "Maintain Aspect"]
        )
        emulator_layout.addRow("Scaling Mode:", self.settings_dialog.scale_box)
        # Frame Skip
        self.settings_dialog.skip_box = QComboBox()
        self.settings_dialog.skip_box.setObjectName("skip_box")
        self.settings_dialog.skip_box.addItems(["Off", "Auto", "1", "2", "3", "4"])
        emulator_layout.addRow("Frame Skip:", self.settings_dialog.skip_box)
        emulator_tab.setLayout(emulator_layout)
        tabs.addTab(emulator_tab, "Emulator")

        #--- AI Settings Tab ---#
        ai_tab = QWidget()
        ai_layout = QFormLayout()
        #temperature settings
        self.settings_dialog.temp_box = QSpinBox()
        self.settings_dialog.temp_box.setObjectName("temp_box")
        self.settings_dialog.temp_box.setRange(0, 200)
        self.settings_dialog.temp_box.setValue(20)
        ai_layout.addRow("Temperature (x0.01):", self.settings_dialog.temp_box)
        #token settings
        self.settings_dialog.max_tokens_box = QSpinBox()
        self.settings_dialog.max_tokens_box.setObjectName("max_tokens_box")
        self.settings_dialog.max_tokens_box.setRange(16, 4096)
        ai_layout.addRow("Max Tokens:", self.settings_dialog.max_tokens_box)
        #history length
        self.settings_dialog.history_box = QSpinBox()
        self.settings_dialog.history_box.setObjectName("history_box")
        self.settings_dialog.history_box.setRange(1, 50)
        ai_layout.addRow("History Length:", self.settings_dialog.history_box)
        #ai update for set frames
        self.settings_dialog.update_rate_box = QSpinBox()
        self.settings_dialog.update_rate_box.setObjectName("update_rate_box")
        self.settings_dialog.update_rate_box.setRange(1, 10)
        ai_layout.addRow("AI Update Every N Frames:", self.settings_dialog.update_rate_box)
        ai_tab.setLayout(ai_layout)
        tabs.addTab(ai_tab, "AI")

        #--- Prompt / Logic Tab ---#
        prompt_tab = QWidget()
        prompt_layout = QFormLayout()
        self.settings_dialog.auto_reload_prompt = QCheckBox("Auto-Reload Prompt Template")
        self.settings_dialog.auto_reload_prompt.setObjectName("auto_reload_prompt")
        prompt_layout.addRow(self.settings_dialog.auto_reload_prompt)
        self.settings_dialog.auto_reload_logic = QCheckBox("Auto-Reload Logic JSON")
        self.settings_dialog.auto_reload_logic.setObjectName("auto_reload_logic")
        prompt_layout.addRow(self.settings_dialog.auto_reload_logic)
        self.settings_dialog.save_prompts = QCheckBox("Save Prompts to File")
        self.settings_dialog.save_prompts.setObjectName("save_prompts")
        prompt_layout.addRow(self.settings_dialog.save_prompts)
        self.settings_dialog.save_responses = QCheckBox("Save AI Responses to File")
        self.settings_dialog.save_responses.setObjectName("save_responses")
        prompt_layout.addRow(self.settings_dialog.save_responses)
        prompt_tab.setLayout(prompt_layout)
        tabs.addTab(prompt_tab, "Prompt/Logic")

        #--- UI Settings Tab ---#
        ui_tab = QWidget()
        ui_layout = QFormLayout()
        self.settings_dialog.theme_box = QComboBox()
        self.settings_dialog.theme_box.setObjectName("theme_box")
        self.settings_dialog.theme_box.addItems(["Light", "Dark", "System"])
        ui_layout.addRow("Theme:", self.settings_dialog.theme_box)
        self.settings_dialog.font_box = QComboBox()
        self.settings_dialog.font_box.setObjectName("font_box")
        self.settings_dialog.font_box.addItems(["Small", "Medium", "Large"])
        ui_layout.addRow("Font Size:", self.settings_dialog.font_box)
        self.settings_dialog.reset_docks = QPushButton("Reset Dock Layout")
        self.settings_dialog.reset_docks.setObjectName("reset_docks")
        ui_layout.addRow(self.settings_dialog.reset_docks)
        ui_tab.setLayout(ui_layout)
        tabs.addTab(ui_tab, "UI")

        #--- Gamepad Settings Tab ---#
        gamepad_tab = QWidget()
        gamepad_layout = QFormLayout()
        self.settings_dialog.detect_button = QPushButton("Detect Gamepads")
        self.settings_dialog.detect_button.setObjectName("detect_button")
        self.settings_dialog.detect_button.clicked.connect(self._detect_gamepads)
        gamepad_layout.addRow(self.settings_dialog.detect_button)
        self.settings_dialog.assign_button = QPushButton("Assign Buttons")
        self.settings_dialog.assign_button.setObjectName("assign_button")
        self.settings_dialog.assign_button.clicked.connect(self._assign_gamepad_buttons)
        gamepad_layout.addRow(self.settings_dialog.assign_button)
        gamepad_tab.setLayout(gamepad_layout)
        tabs.addTab(gamepad_tab, "Gamepad")

        #--- Advanced Settings Tab ---#
        advanced_tab = QWidget()
        advanced_layout = QFormLayout()
        self.settings_dialog.verbose_log = QCheckBox("Enable Verbose Logging")
        self.settings_dialog.verbose_log.setObjectName("verbose_log")
        advanced_layout.addRow(self.settings_dialog.verbose_log)
        self.settings_dialog.raw_context = QCheckBox("Show Raw Emulator Context")
        self.settings_dialog.raw_context.setObjectName("raw_context")
        advanced_layout.addRow(self.settings_dialog.raw_context)
        self.settings_dialog.reset_all = QPushButton("Reset All Settings")
        self.settings_dialog.reset_all.setObjectName("reset_all")
        advanced_layout.addRow(self.settings_dialog.reset_all)
        advanced_tab.setLayout(advanced_layout)
        tabs.addTab(advanced_tab, "Advanced")

        #--- Save / Cancel Buttons ---#
        button_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setObjectName("save_btn")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancel_btn")
        save_btn.clicked.connect(self._save_settings)
        cancel_btn.clicked.connect(self.settings_dialog.close)
        button_row.addWidget(save_btn)
        button_row.addWidget(cancel_btn)
        layout.addLayout(button_row)

        ##settings dialog layout##
        self.settings_dialog.setLayout(layout)

    # ---------------------------------------------------------
    # Save Settings
    # ---------------------------------------------------------
    def _save_settings(self):
        """
            -Saves all AISNES Settings to settings.json
        """
        save_settings_dialog(self.settings_dialog)
        self.settings_dialog.close()


# =========================================================== #
# Gamepad Section                                             #
# =========================================================== #
    # ---------------------------------------------------------
    # Gamepad Detection
    # ---------------------------------------------------------
    def _detect_gamepads(self):
        """
            -Detects connected gamepads
        """
        pads = detect_gamepads()
        QMessageBox.information(self, "Gamepads", "\n".join(pads) or "No gamepads detected.")
        self._update_status_bar()

    # ---------------------------------------------------------
    # Gamepad Button Assignment
    # ---------------------------------------------------------
    def _assign_gamepad_buttons(self):
        """
            -Opens the Gamepad Button Assignment UI
        """
        open_input_mapper(self)


# =========================================================== #
# Player Assignment                                           #
# =========================================================== #
    # ------------------------
    # Assign AI to Player 1
    # ------------------------
    def _assign_ai_to_p1(self):
        """
            -Assigns AI to Player 1 Controller
        """
        if self.selected_controller and self.bridge:
            self.bridge.mind_p1 = self.selected_controller
            self._update_status_bar()

    # -----------------------
    # Assign AI to Player 2
    # -----------------------
    def _assign_ai_to_p2(self):
        """
            -Assigns AI to Player 2 Controller
        """
        if self.selected_controller and self.bridge:
            self.bridge.mind_p2 = self.selected_controller
            self._update_status_bar()

    # -------------------------
    # Remove AI from Player 1
    # -------------------------
    def _remove_ai_from_p1(self):
        """
            -Removes AI from Player 1 Controller
        """
        if self.bridge:
            self.bridge.mind_p1 = None
            self._update_status_bar()

    # -------------------------
    # Remove AI from Player 2
    # -------------------------
    def _remove_ai_from_p2(self):
        """
            -Removes AI from Player 2 Controller
        """
        if self.bridge:
            self.bridge.mind_p2 = None
            self._update_status_bar()


# =========================================================== #
# LLM Section                                                 #
# =========================================================== #
    # ---------------------------------------------------------
    # Load LLM Model
    # ---------------------------------------------------------
    def _load_llm_model(self):
        """
            Loads an LLM from manifest.yaml.
            Does NOT attach it to the emulator automatically.
            User must assign it via the AI menu.
        """
        models = list_available_models()
        if not models:
            QMessageBox.warning(self, "Models", "No models found in manifest.yaml")
            return

        # Let the user pick a model
        model_name, ok = QInputDialog.getItem(
            self,
            "Select LLM Model",
            "Choose a model to load:",
            models,
            0,
            False
        )

        if not ok or not model_name:
            return

        self.selected_model_name = model_name

        # Build controller (always)
        ai_cfg = {}
        if self.current_rom_path:
            ai_cfg = load_ai_config(self.current_rom_path)

        self.selected_controller = build_controller(model_name, ai_cfg)

        QMessageBox.information(
            self,
            "Model Loaded",
            f"Loaded model: {model_name}\n\n"
            "Use the AI menu to assign this model to Player 1 or Player 2."
        )
        self._update_status_bar()

    # ------------------------
    # Open Model Selector
    # ------------------------
    def _open_model_selector(self):
        """ 
            -Opens existing model selection dialog
        """
        self._load_llm_model()
        self._update_status_bar()

# =========================================================== #
# Chat Section                                                #
# =========================================================== #
    # ----------------------------
    # Send Chat Message
    # ----------------------------
    def _send_chat_message(self):
        """
        Sends a message to the currently loaded LLM (preloaded or active).
        """
        # Must have a model loaded
        controller = None

        if hasattr(self, "selected_controller") and self.selected_controller:
            controller = self.selected_controller
        elif self.bridge and self.bridge.mind_p1:
            controller = self.bridge.mind_p1
        else:
            QMessageBox.warning(self, "Chat", "Load an LLM model first.")
            return

        user_msg = self.chat_input.toPlainText().strip()
        if not user_msg:
            return

        # Show user message
        self.chat_history.append(f"<b>You:</b> {user_msg}")
        self.chat_input.clear()

        # Generate response
        try:
            response = controller.llm.generate_raw_llama(prompt=user_msg)
        except Exception as e:
            response = f"[ERROR] {e}"

        # Show LLM response
        self.chat_history.append(f"<b>LLM:</b> {response}")

    # ------------------------
    # Toggle Chat Dock
    # ------------------------
    def _toggle_chat_dock(self):
        self.chat_dock.setVisible(not self.chat_dock.isVisible())
        self._update_status_bar()


# =========================================================== #
# Event Closer                                                #
# =========================================================== #
    # ---------------------------------------------------------
    # Window close behavior
    # ---------------------------------------------------------
    def closeEvent(self, event):
        """
            -Closes the Emulator, and Window
        """
        if self.bridge:
            try:
                self.bridge.stop()
            except Exception as e:
                print(f"[SNESWindow] Error stopping emulator: {e}")
        event.accept()
