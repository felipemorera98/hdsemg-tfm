import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from config import CANALES, NUM_PUNTOS, COLORES_ADC


class PlotWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        self._gl = pg.GraphicsLayoutWidget()
        lay.addWidget(self._gl)

        self.data    = np.zeros((CANALES, NUM_PUNTOS))
        self._curves = []

        for i in range(CANALES):
            p = self._gl.addPlot(title=f"CH {i+1}")
            p.hideAxis('bottom')
            p.setLabel('left', 'µV')   # ← solo esto se añade
            p.setDownsampling(auto=True, mode='peak')  # ← añadir esto
            p.setClipToView(True) 
            color = COLORES_ADC[i // 8]
            self._curves.append(p.plot(pen=pg.mkPen(color=color, width=1)))

            if (i + 1) % 4 == 0:
                self._gl.nextRow()

    def actualizar(self, nuevos_datos: np.ndarray):
        n   = nuevos_datos.shape[1]
        cap = self.data.shape[1]

        if n == 0:
            return

        if n >= cap:
            self.data = nuevos_datos[:, -cap:]
        else:
            self.data = np.roll(self.data, -n, axis=1)
            self.data[:, -n:] = nuevos_datos

        for i, curve in enumerate(self._curves):
            curve.setData(self.data[i])
            
    def limpiar(self):
        """Resetea el buffer de display a cero."""
        self.data = np.zeros_like(self.data)
        for i, curve in enumerate(self._curves):
            curve.setData(self.data[i])