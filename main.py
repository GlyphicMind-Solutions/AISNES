# /AISNES/main.py
# AISNES Entry Point
# Created By: David Kistner (Unconditional Love) at GlyphicMind Solutions LLC.



#system imports
import sys
from PyQt5.QtWidgets import QApplication

#folder imports
from src.gui.snes_window import SNESWindow



# -----------
# Main
# -----------
def main():
    # Start Qt GUI
    app = QApplication(sys.argv)

    # Window will handle ROM selection
    window = SNESWindow()
    window.show()

    sys.exit(app.exec_())

# ----------------------------
# if name = main (for window)
# ----------------------------
if __name__ == "__main__":
    main()

