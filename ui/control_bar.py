from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton,
                              QLabel, QLineEdit, QSlider, QFileDialog)
from PyQt6.QtGui import QIntValidator, QDoubleValidator
from PyQt6.QtCore import Qt


class ControlBar(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(96)          # ← sube de 52 a 96 para dos filas
        self.setLayout(self._build_layout())
        self.set_estilo_grabar(activo=False)
        self.set_estilo_filtro(activo=False)

    def _build_layout(self):
        from PyQt6.QtWidgets import QVBoxLayout
        vlay = QVBoxLayout()
        vlay.setContentsMargins(6, 4, 6, 4)
        vlay.setSpacing(4)
        vlay.addLayout(self._fila_superior())
        vlay.addLayout(self._fila_replay())
        return vlay
    
    

    # ── Fila superior  ──────────────────────────────────────
    def _fila_superior(self):
        lay = QHBoxLayout()
        lay.setSpacing(10)

        self.lbl_conexion = QLabel("⬤  Sin señal")
        self.lbl_conexion.setFixedWidth(130)
        self.lbl_conexion.setStyleSheet("font-size:13px; font-weight:bold; color:#e74c3c;")

        self.btn_desconectar = QPushButton("🔌")
        self.btn_desconectar.setFixedSize(65, 32)
        self.btn_desconectar.setToolTip("Desconectar dispositivo")
        self.btn_desconectar.setStyleSheet(self._css("#c0392b","#a93226","#7b241c"))

        self.btn_iniciar_lectura = QPushButton("▶ Iniciar ADCs")
        self.btn_iniciar_lectura.setFixedSize(85, 32)
        self.btn_iniciar_lectura.setEnabled(False)
        self.btn_iniciar_lectura.setStyleSheet(
            self._css("#27ae60","#1e8449","#196f3d"))
        lay.addStretch()   # ← empuja el reset al extremo derecho

        self.btn_reset = QPushButton("🔄 Reset")
        self.btn_reset.setFixedSize(60, 32)
        self.btn_reset.setEnabled(False)
        self.btn_reset.setToolTip("Reset completo de los ADCs — usar solo en caso de fallo")
        self.btn_reset.setStyleSheet(self._css("#7f8c8d","#636e72","#4a4a4a"))
        lay.addWidget(self.btn_reset)

        sep0 = QLabel("|"); sep0.setStyleSheet("color:#555; font-size:20px;")

        self.btn_grabar = QPushButton("⏺  Iniciar grabación")
        self.btn_grabar.setFixedSize(130, 32)

        sep1 = QLabel("|"); sep1.setStyleSheet("color:#555; font-size:20px;")

        self.inp_orden = QLineEdit("4"); self.inp_orden.setFixedSize(45, 32)
        self.inp_orden.setValidator(QIntValidator(1, 10))
        self.inp_orden.setToolTip("Orden Butterworth (1–10)")

        self.inp_flow = QLineEdit("20"); self.inp_flow.setFixedSize(55, 32)
        self.inp_flow.setValidator(QDoubleValidator(0.1, 4000.0, 1))
        self.inp_flow.setToolTip("Frecuencia de corte inferior (Hz)")

        self.inp_fhigh = QLineEdit("500"); self.inp_fhigh.setFixedSize(55, 32)
        self.inp_fhigh.setValidator(QDoubleValidator(0.1, 4000.0, 1))
        self.inp_fhigh.setToolTip("Frecuencia de corte superior (Hz)")

        self.btn_filtro = QPushButton("Aplicar filtro")
        self.btn_filtro.setFixedSize(95, 32) 

        sep2 = QLabel("|"); sep2.setStyleSheet("color:#555; font-size:20px;")

        self.btn_notch_60  = QPushButton("60 Hz"); self.btn_notch_60.setFixedSize(55, 32)
        self.btn_notch_50  = QPushButton("50 Hz"); self.btn_notch_50.setFixedSize(55, 32)
        self.btn_notch_off = QPushButton("OFF");   self.btn_notch_off.setFixedSize(45, 32)
        self.btn_notch_60.setStyleSheet(self._css("#e67e22","#d35400","#a04000"))
        self.btn_notch_50.setStyleSheet(self._css("#e67e22","#d35400","#a04000"))
        self.btn_notch_off.setStyleSheet(self._css("#7f8c8d","#636e72","#4a4a4a"))

        self.lbl_estado = QLabel("En espera")
        self.lbl_estado.setStyleSheet("font-size:12px; color:#888;")
        self.lbl_filas = QLabel("")
        self.lbl_filas.setStyleSheet("font-size:12px; color:#888;")

        for w in [self.lbl_conexion, self.btn_desconectar, self.btn_iniciar_lectura, sep0, self.btn_grabar, sep1,
                QLabel("Orden:"), self.inp_orden,
                QLabel("F. baja:"), self.inp_flow,
                QLabel("F. alta:"), self.inp_fhigh,
                self.btn_filtro, sep2,
                QLabel("Notch:"), self.btn_notch_60,
                self.btn_notch_50, self.btn_notch_off]:
            lay.addWidget(w)
        lay.addSpacing(8)
        lay.addWidget(self.lbl_estado)
        lay.addWidget(self.lbl_filas)  # ← antes del stretch
        lay.addStretch()               # ← empuja Reset al extremo derecho
        lay.addWidget(self.btn_reset)  # ← solo en el extremo derecho
        return lay

    # ── Fila inferior — REPLAY ────────────────────────────────────────────────
    def _fila_replay(self):
        lay = QHBoxLayout()
        lay.setSpacing(8)

        lbl = QLabel("Replay:")
        lbl.setStyleSheet("font-size:12px; color:#aaa;")

        self.btn_abrir = QPushButton("📂 Abrir CSV")
        self.btn_abrir.setFixedSize(110, 28)
        self.btn_abrir.setStyleSheet(self._css("#8e44ad","#7d3c98","#6c3483"))

        self.btn_play = QPushButton("▶ Play")
        self.btn_play.setFixedSize(80, 28)
        self.btn_play.setEnabled(False)
        self.btn_play.setStyleSheet(self._css("#27ae60","#1e8449","#196f3d"))

        self.btn_pausa = QPushButton("⏸ Pausa")
        self.btn_pausa.setFixedSize(80, 28)
        self.btn_pausa.setEnabled(False)
        self.btn_pausa.setStyleSheet(self._css("#e67e22","#d35400","#a04000"))

        self.btn_stop_replay = QPushButton("⏹ Stop")
        self.btn_stop_replay.setFixedSize(70, 28)
        self.btn_stop_replay.setEnabled(False)
        self.btn_stop_replay.setStyleSheet(self._css("#e74c3c","#c0392b","#922b21"))
        self.btn_desconectar.setToolTip("Conectar / Desconectar dispositivo")

        lbl_vel = QLabel("Velocidad:")
        lbl_vel.setStyleSheet("font-size:12px; color:#aaa;")

        self.btn_vel = QPushButton("x1")
        self.btn_vel.setFixedSize(45, 28)
        self.btn_vel.setStyleSheet(self._css("#2980b9","#2471a3","#1a5276"))

        # Barra de progreso del archivo
        self.slider_replay = QSlider(Qt.Orientation.Horizontal)
        self.slider_replay.setRange(0, 1000)
        self.slider_replay.setValue(0)
        self.slider_replay.setEnabled(False)
        self.slider_replay.setFixedWidth(200)

        self.lbl_replay_info = QLabel("Sin archivo")
        self.lbl_replay_info.setStyleSheet("font-size:11px; color:#888;")

        for w in [lbl, self.btn_abrir, self.btn_play, self.btn_pausa,
                  self.btn_stop_replay, lbl_vel, self.btn_vel,
                  self.slider_replay, self.lbl_replay_info]:
            lay.addWidget(w)
        lay.addStretch()
        return lay

    # ── Helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _css(c1, c2, c3, borde=False):
        b = "border:2px solid white;" if borde else "border:none;"
        return f"""
            QPushButton {{
                background-color:{c1}; color:white;
                font-size:12px; font-weight:bold;
                border-radius:5px; {b}
            }}
            QPushButton:hover   {{ background-color:{c2}; }}
            QPushButton:pressed {{ background-color:{c3}; }}
            QPushButton:disabled {{ background-color:#444; color:#888; }}
        """

    def set_estilo_grabar(self, activo: bool):
        if activo:
            self.btn_grabar.setStyleSheet(self._css("#e74c3c","#c0392b","#922b21", borde=True))
        else:
            self.btn_grabar.setStyleSheet(self._css("#2ecc71","#27ae60","#1e8449"))

    def set_estilo_filtro(self, activo: bool):
        if activo:
            self.btn_filtro.setStyleSheet(self._css("#8e44ad","#7d3c98","#6c3483", borde=True))
        else:
            self.btn_filtro.setStyleSheet(self._css("#3498db","#2980b9","#1a6390"))

    def bloquear_inputs_filtro(self, bloquear: bool):
        for w in [self.inp_orden, self.inp_flow, self.inp_fhigh]:
            w.setEnabled(not bloquear)

    def set_conexion(self, conectado: bool):
        if conectado:
            self.lbl_conexion.setText("⬤  Conectado")
            self.lbl_conexion.setStyleSheet("font-size:13px; font-weight:bold; color:#2ecc71;")
        else:
            self.lbl_conexion.setText("⬤  Sin señal")
            self.lbl_conexion.setStyleSheet("font-size:13px; font-weight:bold; color:#e74c3c;")

    def set_estado(self, grabando: bool, filtro: bool, f_low="", f_high=""):
        partes = []
        if grabando: partes.append("⏺ Grabando")
        if filtro:   partes.append(f"🎛 {f_low}–{f_high} Hz")
        if partes:
            self.lbl_estado.setText("  |  ".join(partes))
            self.lbl_estado.setStyleSheet("font-size:12px; color:#f1c40f; font-weight:bold;")
        else:
            self.lbl_estado.setText("En espera")
            self.lbl_estado.setStyleSheet("font-size:12px; color:#888;")

    def set_error(self, mensaje: str):
        self.lbl_estado.setText(f"⚠ {mensaje}")
        self.lbl_estado.setStyleSheet("font-size:12px; color:#e67e22;")

    def set_contador(self, n: int):
        self.lbl_filas.setText(f"Muestras: {n:,}")