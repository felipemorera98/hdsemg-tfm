import numpy as np
import pandas as pd
from pathlib import Path


class CsvReplay:
    """Lee un CSV grabado y lo reproduce al ritmo original o acelerado."""

    def __init__(self):
        self._datos: np.ndarray | None = None  # shape (N, 32)
        self._indice   = 0
        self._velocidad = 1
        self.activo    = False
        self.pausado   = False
        self.nombre    = ""
        self.total     = 0

    @property
    def progreso(self) -> float:
        """Devuelve progreso entre 0.0 y 1.0."""
        if self.total == 0:
            return 0.0
        return min(self._indice / self.total, 1.0)

    @property
    def velocidad(self) -> int:
        return self._velocidad

    @velocidad.setter
    def velocidad(self, v: int):
        self._velocidad = max(1, v)

    def cargar(self, path: str) -> bool:
        """Carga el CSV en memoria. Devuelve True si tuvo éxito."""
        try:
            df = pd.read_csv(path)
            # Extraer solo las columnas CH1..CH32
            cols_ch = [c for c in df.columns if c.startswith('CH')]
            if len(cols_ch) != 32:
                return False
            self._datos  = df[cols_ch].to_numpy(dtype=np.float32)
            self._indice = 0
            self.total   = len(self._datos)
            self.nombre  = Path(path).name
            self.activo  = False
            self.pausado = False
            return True
        except Exception as e:
            print(f"❌ Error cargando CSV: {e}")
            return False

    def play(self):
        if self._datos is not None:
            self.activo  = True
            self.pausado = False

    def pausar(self):
        self.pausado = not self.pausado

    def detener(self):
        self.activo  = False
        self.pausado = False
        self._indice = 0

    def siguiente_bloque(self, samples_por_tick: int) -> np.ndarray | None:
        if not self.activo or self.pausado or self._datos is None:
            return None

        # Con velocidades < 1 puede salir 0 — mínimo siempre 1
        n = max(1, int(samples_por_tick * self._velocidad))
        fin = self._indice + n

        if self._indice >= self.total:
            self.activo = False
            return None

        bloque = self._datos[self._indice:fin].T
        self._indice = min(fin, self.total)
        return bloque
    @property
    def velocidad(self) -> float:
        return self._velocidad

    @velocidad.setter
    def velocidad(self, v: float):   # ← float en vez de int
        self._velocidad = v
    
    def seek(self, fraccion: float):
        """Salta a una posición (0.0 - 1.0) del archivo."""
        if self._datos is not None:
            self._indice = int(fraccion * self.total)