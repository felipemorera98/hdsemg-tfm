from dataclasses import dataclass, field
import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi

from config import FS, CANALES


@dataclass
class FiltroPasaBanda:
    orden:  int
    f_low:  float
    f_high: float
    sos:    np.ndarray = field(init=False, repr=False)
    zi:     list       = field(init=False, repr=False)

    def __post_init__(self):
        self.sos = butter(
            self.orden,
            [self.f_low, self.f_high],
            btype='bandpass',
            fs=FS,
            output='sos'
        )
        zi_base = sosfilt_zi(self.sos)
        self.zi = [zi_base.copy() for _ in range(CANALES)]

    def aplicar(self, bloque: np.ndarray) -> np.ndarray:
        salida = bloque.copy()
        for i in range(CANALES):
            salida[i], self.zi[i] = sosfilt(self.sos, bloque[i], zi=self.zi[i])
        return salida


def validar_parametros(orden: int, f_low: float, f_high: float) -> str | None:
    nyquist = FS / 2.0  # límite físico real, no artificial

    if not (1 <= orden <= 10):
        return "El orden debe estar entre 1 y 10"
    if f_low <= 0:
        return "F. baja debe ser mayor que 0 Hz"
    if f_low >= f_high:
        return "F. baja debe ser menor que F. alta"
    if f_high >= nyquist:
        return f"F. alta debe ser menor que Nyquist ({nyquist} Hz) — sube FS en config.py si necesitas más"
    return None