# HD-sEMG 32-Channel Acquisition System — TFM UC3M

Sistema de electromiografía de alta densidad (HD-sEMG) de 32 canales 
ampliable, desarrollado como Trabajo de Fin de Máster en el 
Máster Universitario en Robótica y Automatización de la UC3M.

## Estructura del repositorio

- `ADS1298/` — Emulador hardware del ADS1298 para Arduino 33 BLE Sense
- `dsp/` — Filtros digitales (pasa-banda Butterworth)
- `recording/` — Grabación de datos en CSV
- `replay/` — Reproducción de grabaciones
- `ui/` — Interfaz gráfica (PyQt6 + pyqtgraph)
- `main.py` — Punto de entrada de la aplicación
- `config.py` — Parámetros de configuración
- `serial_reader.py` — Lectura del puerto serie USB CDC
- `decoder.py` — Decodificación de tramas ADS1298

## Requisitos
