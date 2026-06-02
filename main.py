import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import pyqtgraph as pg
import serial_reader
from ui.main_window import MainWindow

pg.setConfigOptions(
    antialias=False,    # desactiva suavizado — el más costoso
    useOpenGL=True      # usa GPU en vez de CPU para renderizar
)

def main():
    #serial_reader.iniciar()

    app = QApplication(sys.argv)
    window = MainWindow()

    # Fuerza el tamaño completo de la pantalla disponible
    screen = app.primaryScreen().availableGeometry()
    window.setGeometry(screen)
    window.setWindowState(Qt.WindowState.WindowMaximized)
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()