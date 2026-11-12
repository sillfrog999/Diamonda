import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from diamonda.ui.main_window import MainWindow

BASE_DIR = Path(__file__).resolve().parent

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Diamonda")
    app.setOrganizationName("Diamonda")
    window = MainWindow(BASE_DIR)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
