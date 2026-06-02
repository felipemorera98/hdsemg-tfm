import time
import numpy as np
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QFileDialog

import serial_reader
from config import MAX_PAQUETES, TIMER_MS, LSB_UV, FS, MAX_REPLAY_SAMPLES
from serial_reader import cola_datos
from decoder import decodificar_paquete
from dsp.filters import FiltroPasaBanda, validar_parametros
from recording.csv_recorder import CsvRecorder
from replay.csv_replay import CsvReplay
from ui.control_bar import ControlBar
from ui.plot_widget import PlotWidget

_SAMPLES_POR_TICK = max(1, int(TIMER_MS * FS / 1000))
_VELOCIDADES      = [0.25, 0.5, 0.75, 1]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitor Médico DAQ — 32 Canales")

        self._grabador = CsvRecorder(carpeta="grabaciones")
        self._filtro:  FiltroPasaBanda | None = None
        self._replay   = CsvReplay()
        self._vel_idx  = 0
        self._slider_dragging = False
        self._leyendo = False
        self._estado_conexion_anterior: bool | None = None

        root = QWidget()
        self.setCentralWidget(root)
        vlay = QVBoxLayout(root)
        vlay.setContentsMargins(6, 6, 6, 4)
        vlay.setSpacing(4)

        self._bar   = ControlBar()
        self._plots = PlotWidget()
        vlay.addWidget(self._bar)
        vlay.addWidget(self._plots)

        # — Señales adquisición —
        self._bar.btn_grabar.clicked.connect(self._toggle_grabacion)
        self._bar.btn_filtro.clicked.connect(self._toggle_filtro)
        self._bar.btn_notch_60.clicked.connect(lambda: self._enviar_notch("N60"))
        self._bar.btn_notch_50.clicked.connect(lambda: self._enviar_notch("N50"))
        self._bar.btn_notch_off.clicked.connect(lambda: self._enviar_notch("NOFF"))
        self._bar.btn_desconectar.clicked.connect(self._toggle_conexion)
        self._bar.btn_reset.clicked.connect(self._reset_adcs)
        self._bar.btn_iniciar_lectura.clicked.connect(self._toggle_lectura)

        # — Señales replay —
        self._bar.btn_abrir.clicked.connect(self._abrir_csv)
        self._bar.btn_play.clicked.connect(self._replay_play)
        self._bar.btn_pausa.clicked.connect(self._replay_pausa)
        self._bar.btn_stop_replay.clicked.connect(self._replay_stop)
        self._bar.btn_vel.clicked.connect(self._cambiar_velocidad)
        self._bar.slider_replay.sliderPressed.connect(self._slider_pressed)
        self._bar.slider_replay.sliderReleased.connect(self._slider_released)
        self._bar.slider_replay.valueChanged.connect(self._slider_movido)
        self._actualizar_estilo_notch("N60")

        self._timer = QTimer()
        self._timer.timeout.connect(self._actualizar)
        self._timer.start(TIMER_MS)

    # ── Grabación ─────────────────────────────────────────────────────────────
    def _toggle_grabacion(self):
        if not self._grabador.activo:
            self._grabador.iniciar()
            self._bar.btn_grabar.setText("⏹ Parar")
            self._bar.set_estilo_grabar(activo=True)
        else:
            self._grabador.detener()
            self._bar.btn_grabar.setText("⏺ Grabar")     # ← al detener
            self._bar.set_estilo_grabar(activo=False)
            self._bar.set_contador(0)
        self._refrescar_estado()

    # ── Filtro paso-banda ──────────────────────────────────────────────────────
    def _toggle_filtro(self):
        if self._filtro is None:
            try:
                orden  = int(self._bar.inp_orden.text())
                f_low  = float(self._bar.inp_flow.text().replace(',', '.'))
                f_high = float(self._bar.inp_fhigh.text().replace(',', '.'))
            except ValueError:
                self._bar.set_error("Valores no numéricos")
                return
            error = validar_parametros(orden, f_low, f_high)
            if error:
                self._bar.set_error(error)
                return
            self._filtro = FiltroPasaBanda(orden, f_low, f_high)
            self._bar.btn_filtro.setText("Cancelar filtro")
            self._bar.set_estilo_filtro(activo=True)
            self._bar.bloquear_inputs_filtro(True)
        else:
            self._filtro = None
            self._bar.btn_filtro.setText("Aplicar filtro")
            self._bar.set_estilo_filtro(activo=False)
            self._bar.bloquear_inputs_filtro(False)
        self._refrescar_estado()

    # ── Notch ─────────────────────────────────────────────────────────────────
    def _enviar_notch(self, cmd: str):
        serial_reader.enviar_comando(cmd)
        self._actualizar_estilo_notch(cmd)

    def _actualizar_estilo_notch(self, activo: str):
        # Colores: activo = naranja brillante con borde, inactivo = gris
        estilo_activo  = self._bar._css("#e67e22","#d35400","#a04000", borde=True)
        estilo_inactivo = self._bar._css("#555555","#444444","#333333")
        estilo_off_activo = self._bar._css("#e74c3c","#c0392b","#922b21", borde=True)

        if activo == "N60":
            self._bar.btn_notch_60.setStyleSheet(estilo_activo)
            self._bar.btn_notch_50.setStyleSheet(estilo_inactivo)
            self._bar.btn_notch_off.setStyleSheet(estilo_inactivo)
        elif activo == "N50":
            self._bar.btn_notch_60.setStyleSheet(estilo_inactivo)
            self._bar.btn_notch_50.setStyleSheet(estilo_activo)
            self._bar.btn_notch_off.setStyleSheet(estilo_inactivo)
        elif activo == "NOFF":
            self._bar.btn_notch_60.setStyleSheet(estilo_inactivo)
            self._bar.btn_notch_50.setStyleSheet(estilo_inactivo)
            self._bar.btn_notch_off.setStyleSheet(estilo_off_activo)

    # ── Conexión ──────────────────────────────────────────────────────────────
    def _toggle_conexion(self):
        if serial_reader.conectado or serial_reader._activo:
            # Apagar ADCs antes de desconectar
            if self._leyendo:
                serial_reader.detener_lectura()
                self._leyendo = False
            serial_reader.desconectar()
            self._bar.set_conexion(False)
            self._estado_conexion_anterior = False
            self._bar.btn_iniciar_lectura.setText("▶ Iniciar ADCs")
            self._bar.btn_iniciar_lectura.setStyleSheet(
                self._bar._css("#27ae60","#1e8449","#196f3d"))
            self._bar.btn_desconectar.setToolTip("Conectar dispositivo")
        else:
            serial_reader.iniciar_reconexion()
            self._bar.btn_desconectar.setToolTip("Desconectar dispositivo")
    
    def _toggle_lectura(self):
        if not self._leyendo:
            serial_reader.iniciar_lectura()
            self._leyendo = True
            self._bar.btn_iniciar_lectura.setText("⏸ Detener ADCs")
            self._bar.btn_iniciar_lectura.setStyleSheet(
                self._bar._css("#e74c3c","#c0392b","#922b21", borde=True))
        else:
            serial_reader.detener_lectura()
            self._leyendo = False
            self._bar.btn_iniciar_lectura.setText("▶ Iniciar ADCs")
            self._bar.btn_iniciar_lectura.setStyleSheet(
            self._bar._css("#27ae60","#1e8449","#196f3d"))
            
    def _reset_adcs(self):
        serial_reader.reset_adcs()

        # Resetear estado interno
        self._leyendo = False
        if self._grabador.activo:
            self._grabador.detener()

        # Resetear todas las UI
        self._plots.limpiar()
        self._bar.btn_iniciar_lectura.setText("▶ Iniciar ADCs")
        self._bar.btn_iniciar_lectura.setStyleSheet(
            self._bar._css("#27ae60","#1e8449","#196f3d"))
        self._bar.btn_grabar.setText("⏺  Iniciar grabación")
        self._bar.set_estilo_grabar(activo=False)
        self._bar.set_contador(0)

        # Feedback visual
        self._bar.btn_reset.setStyleSheet(
            self._bar._css("#e74c3c","#c0392b","#922b21", borde=True))
        self._bar.lbl_estado.setText("🔄 Reset ejecutado")
        self._bar.lbl_estado.setStyleSheet(
            "font-size:12px; color:#e74c3c; font-weight:bold;")
        QTimer.singleShot(1500, self._post_reset)

    
    def _post_reset(self):
        self._bar.btn_reset.setStyleSheet(
            self._bar._css("#7f8c8d","#636e72","#4a4a4a"))
        self._refrescar_estado()

    # ── Replay ────────────────────────────────────────────────────────────────
    def _abrir_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo de datos", "grabaciones", "CSV (*.csv)"
        )
        if not path:
            return
        if self._replay.cargar(path):
            serial_reader.desconectar()
            self._bar.set_conexion(False)
            self._estado_conexion_anterior = False
            self._bar.lbl_replay_info.setText(
                f"{self._replay.nombre}  ({self._replay.total:,} muestras)"
            )
            self._bar.btn_play.setEnabled(True)
            self._bar.btn_stop_replay.setEnabled(True)
            self._bar.slider_replay.setEnabled(True)
            self._bar.slider_replay.setValue(0)
        else:
            self._bar.lbl_replay_info.setText("⚠ Error al cargar el archivo")

    def _replay_play(self):
        if not self._replay.activo:
            self._replay.play()
            self._bar.btn_play.setEnabled(False)
            self._bar.btn_pausa.setEnabled(True)

    def _replay_pausa(self):
        self._replay.pausar()
        pausado = self._replay.pausado
        self._bar.btn_pausa.setText("▶ Reanudar" if pausado else "⏸ Pausa")

    def _replay_stop(self):
        self._replay.detener()
        self._bar.btn_play.setEnabled(True)
        self._bar.btn_pausa.setEnabled(False)
        self._bar.btn_pausa.setText("⏸ Pausa")
        self._bar.slider_replay.setValue(0)
        self._bar.lbl_replay_info.setText(
            f"{self._replay.nombre}  ({self._replay.total:,} muestras)"
        )
        serial_reader.iniciar_reconexion()

    def _cambiar_velocidad(self):
        self._vel_idx = (self._vel_idx + 1) % len(_VELOCIDADES)
        v = _VELOCIDADES[self._vel_idx]
        self._replay.velocidad = v
        self._bar.btn_vel.setText(f"x{v:g}")

    def _slider_pressed(self):
        self._slider_dragging = True

    def _slider_released(self):
        fraccion = self._bar.slider_replay.value() / 1000.0
        self._replay.seek(fraccion)
        self._slider_dragging = False

    def _slider_pressed(self):
        self._slider_dragging = True
        # Pausar mientras arrastra para control preciso
        if self._replay.activo and not self._replay.pausado:
            self._replay.pausado = True
            self._slider_pauso_replay = True
        else:
            self._slider_pauso_replay = False

    def _slider_movido(self, valor: int):
        if not self._slider_dragging:
            return

        fraccion = valor / 1000.0
        self._replay.seek(fraccion)

        if self._replay._datos is None:
            return

        idx = min(self._replay._indice, self._replay.total - 1)
        if idx < 0:
            return

        # Mostrar ventana de 500 muestras centrada en el índice actual
        inicio = max(0, idx - 250)
        fin    = min(self._replay.total, inicio + 500)
        ventana = self._replay._datos[inicio:fin].T  # (32, N)

        if ventana.shape[1] == 0:
            return

        if self._filtro is not None:
            ventana = self._filtro.aplicar(ventana)

        self._plots.actualizar(ventana)

        pct = fraccion * 100
        self._bar.lbl_replay_info.setText(
            f"{self._replay.nombre}  "
            f"{idx:,}/{self._replay.total:,}  "
            f"({pct:.1f}%)"
        )

    def _slider_released(self):
        fraccion = self._bar.slider_replay.value() / 1000.0
        self._replay.seek(fraccion)
        self._slider_dragging = False
        # Reanudar si estaba reproduciendo antes de arrastrar
        if hasattr(self, '_slider_pauso_replay') and self._slider_pauso_replay:
            self._replay.pausado = False

    # ── Bucle principal ───────────────────────────────────────────────────────
    def _actualizar(self):
        estado_actual = serial_reader.conectado
        if estado_actual != self._estado_conexion_anterior:
            self._bar.set_conexion(estado_actual)
            self._bar.btn_iniciar_lectura.setEnabled(estado_actual)
            self._bar.btn_reset.setEnabled(estado_actual)
            if not estado_actual:
                self._leyendo = False
                self._bar.btn_iniciar_lectura.setText("▶ Iniciar ADCs")
                self._bar.btn_iniciar_lectura.setStyleSheet(
                    self._bar._css("#27ae60","#1e8449","#196f3d")
                )
            self._estado_conexion_anterior = estado_actual

        # Modo replay
        if self._replay.activo:
            limite = max(1, int(MAX_REPLAY_SAMPLES / max(self._replay.velocidad, 0.25)))
            nuevos = self._replay.siguiente_bloque(min(_SAMPLES_POR_TICK, limite))

            if nuevos is None:
                if not self._replay.activo:
                    self._replay_stop()
                return

            if not self._slider_dragging:
                self._bar.slider_replay.setValue(int(self._replay.progreso * 1000))
                self._bar.lbl_replay_info.setText(
                    f"{self._replay.nombre}  "
                    f"{self._replay._indice:,}/{self._replay.total:,}  "
                    f"({self._replay.progreso * 100:.1f}%)"
                )

            if self._filtro is not None:
                nuevos = self._filtro.aplicar(nuevos)

            self._plots.actualizar(nuevos)
            return

        # Modo en vivo
        n = min(len(cola_datos), MAX_PAQUETES)
        if n == 0:
            return

        nuevos = np.zeros((32, n))
        t_base = time.time()

        for idx in range(n):
            paquete = cola_datos.popleft()
            valores = decodificar_paquete(paquete)
            for ch, v in enumerate(valores):
                nuevos[ch, idx] = v
            if self._grabador.activo:
                self._grabador.escribir(t_base + idx * 0.001, valores)

        if self._grabador.activo:
            self._bar.set_contador(self._grabador.muestras)

        nuevos = nuevos * LSB_UV

        if self._filtro is not None:
            nuevos = self._filtro.aplicar(nuevos)

        self._plots.actualizar(nuevos)

    # ── Estado ────────────────────────────────────────────────────────────────
    def _refrescar_estado(self):
        self._bar.set_estado(
            grabando=self._grabador.activo,
            filtro=self._filtro is not None,
            f_low=self._bar.inp_flow.text(),
            f_high=self._bar.inp_fhigh.text(),
        )

    

    def closeEvent(self, event):
        if self._grabador.activo:
            self._grabador.detener()
        serial_reader.desconectar()
        event.accept()