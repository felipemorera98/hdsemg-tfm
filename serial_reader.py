import threading
import time
import serial
from collections import deque

from config import PUERTO, BAUDRATE, FRAME_SIZE, SYNC_BYTE

cola_datos: deque = deque(maxlen=2000)
conectado:  bool  = False
_puerto:    serial.Serial | None = None
_hilo:      threading.Thread | None = None
_activo:    bool  = False   # ← nueva bandera: False = hilo se detiene


def _leer_serial():
    global conectado, _puerto, _activo

    while _activo:   # ← condición del bucle principal
        try:
            _puerto = serial.Serial(
                PUERTO, BAUDRATE, timeout=0.1,
                dsrdtr=False, rtscts=False
            )
            _puerto.dtr = False
            _puerto.rts = False
            conectado = True
            print(f"✅ Serial conectado en {PUERTO}")
            buffer = bytearray()

            while _activo:   # ← también en el bucle interno
                n = _puerto.in_waiting
                if n > 0:
                    buffer.extend(_puerto.read(n))
                    while len(buffer) >= FRAME_SIZE:
                        if buffer[0] == SYNC_BYTE and buffer[81] == SYNC_BYTE:
                            cola_datos.append(bytes(buffer[:FRAME_SIZE]))
                            del buffer[:FRAME_SIZE]
                        else:
                            del buffer[0:1]
                else:
                    time.sleep(0.001)

        except serial.SerialException:
            if conectado:
                print(f"⚠ Dispositivo desconectado de {PUERTO}")
            conectado = False
            _puerto   = None
            if _activo:
                time.sleep(2)  # solo reintenta si NO fue desconexión manual

        except Exception as e:
            conectado = False
            _puerto   = None
            print(f"❌ Error serial: {e}")
            if _activo:
                time.sleep(2)


def desconectar():
    """Cierra el puerto y detiene el hilo — no reintenta."""
    global conectado, _puerto, _activo
    _activo = False          # ← el hilo sale del while y no vuelve
    try:
        if _puerto and _puerto.is_open:
            _puerto.close()
    except Exception:
        pass
    conectado = False
    _puerto   = None
    print("🔌 Dispositivo desconectado")


def iniciar_reconexion():
    """Reactiva el hilo para volver al modo en vivo."""
    global _activo, _hilo
    _activo = True
    _hilo   = threading.Thread(target=_leer_serial, daemon=True)
    _hilo.start()
    print(f"🔄 Reintentando conexión en {PUERTO}...")


def enviar_comando(comando: str):
    try:
        if _puerto and _puerto.is_open:
            _puerto.write(f"{comando}\n".encode())
    except Exception as e:
        print(f"❌ Error enviando comando: {e}")

def iniciar_lectura():
    try:
        if _puerto and _puerto.is_open:
            _puerto.write(b"START\n")
            time.sleep(0.05)
            print("▶ Adquisición iniciada")
    except Exception as e:
        print(f"❌ Error: {e}")

def detener_lectura():
    try:
        if _puerto and _puerto.is_open:
            _puerto.write(b"STOP\n")
            time.sleep(0.05)
            print("⏸ Adquisición detenida")
    except Exception as e:
        print(f"❌ Error: {e}")

def reset_adcs():
    try:
        if _puerto and _puerto.is_open:
            _puerto.write(b"RESET\n")
            time.sleep(0.05)
            print("🔄 Reset enviado")
    except Exception as e:
        print(f"❌ Error: {e}")

def iniciar():
    global _hilo, _activo
    _activo = True
    _hilo   = threading.Thread(target=_leer_serial, daemon=True)
    _hilo.start()