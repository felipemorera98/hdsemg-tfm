import csv
from datetime import datetime
from pathlib import Path


class CsvRecorder:
    """Gestiona la apertura, escritura y cierre del archivo CSV."""

    def __init__(self, carpeta: str = "."):
        self._archivo   = None
        self._writer    = None
        self._contador  = 0
        self._carpeta   = Path(carpeta)
        self.nombre_archivo: str = ""

    @property
    def activo(self) -> bool:
        return self._archivo is not None

    @property
    def muestras(self) -> int:
        return self._contador

    def iniciar(self) -> str:
        """Abre un nuevo archivo CSV. Devuelve el nombre creado."""
        self._carpeta.mkdir(parents=True, exist_ok=True)
        self.nombre_archivo = str(
            self._carpeta / f"daq_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        self._archivo  = open(self.nombre_archivo, 'w', newline='')
        self._writer   = csv.writer(self._archivo)
        self._contador = 0
        cabecera = ['timestamp'] + [f'CH{i+1}' for i in range(32)]
        self._writer.writerow(cabecera)
        print(f"⏺ Grabando → {self.nombre_archivo}")
        return self.nombre_archivo

    def escribir(self, timestamp: float, valores: list[int]):
        """Escribe una fila con timestamp + 32 valores."""
        if self._writer:
            self._writer.writerow([f"{timestamp:.6f}"] + valores)
            self._contador += 1

    def detener(self) -> int:
        """Cierra el archivo y devuelve el total de muestras grabadas."""
        if self._archivo:
            self._archivo.flush()
            self._archivo.close()
            self._archivo  = None
            self._writer   = None
        total = self._contador
        print(f"⏹ Grabación detenida — {total} muestras")
        return total