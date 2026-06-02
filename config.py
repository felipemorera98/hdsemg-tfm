PUERTO   = 'COM4'
BAUDRATE = 115200
FS       = 4000
CANALES  = 32
FRAME_SIZE = 108
SYNC_BYTE  = 192
MAX_REPLAY_SAMPLES = 500 
# Conversión ADC → µV
VREF_V    = 2.4    # Tensión de referencia (V)
GANANCIA  = 1     # Ganancia del PGA
BITS      = 24     # Resolución del ADC
LSB_UV    = (2 * VREF_V / GANANCIA) / (2 ** (BITS - 1)) * 1e6  # µV/count ≈ 0.0477 µV

# Rango Y para EMG superficial (ajusta si usas electrodos de aguja)
EMG_RANGO_UV = 5000   # ±5000 µV = ±5 mV

# Visualización
NUM_PUNTOS   = 500
MAX_PAQUETES = 200
TIMER_MS     = 40

COLORES_ADC = [
    (255, 100, 100),
    (100, 255, 100),
    (100, 100, 255),
    (255, 255, 100),
]