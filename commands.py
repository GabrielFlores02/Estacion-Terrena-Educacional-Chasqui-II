from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QTextEdit, QHBoxLayout
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame
import sys

class CubeSatInterface(QWidget):
    def _init_(self):
        super()._init_()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("CubeSat Control Interface")
        self.setGeometry(100, 100, 400, 400)
        layout = QVBoxLayout()
        
        # Modo Label
        self.mode_label = QLabel("Modo: Normal", self)
        layout.addWidget(self.mode_label)
        
        # Dropdown para cambiar modo
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Normal", "Emergencia", "Apagado"])
        self.mode_selector.currentTextChanged.connect(self.change_mode)
        layout.addWidget(self.mode_selector)
        
        # Subsistemas y Sensores
        self.subsystems = {"OBC": None, "EPC": None, "COMM": None, "ADCS": None}
        self.sensors = {"UV": None, "Temperatura": None, "GPS": None, "Aceleracion": None}
        
        layout.addWidget(QLabel("Subsistemas"))
        layout.addLayout(self.create_leds(self.subsystems))
        
        layout.addWidget(QLabel("Sensores"))
        layout.addLayout(self.create_leds(self.sensors))
        
        # Área de comandos
        layout.addWidget(QLabel("Comandos:"))
        self.command_box = QTextEdit()
        self.command_box.setStyleSheet("background-color: black; color: white;")
        layout.addWidget(self.command_box)
        
        # Botón de enviar comandos
        self.send_button = QPushButton("Enviar Comandos")
        layout.addWidget(self.send_button)
        
        self.setLayout(layout)
    
    def create_leds(self, items):
        layout = QHBoxLayout()
        for key in items:
            led = QFrame()
            led.setFixedSize(20, 20)
            led.setStyleSheet("background-color: red; border-radius: 10px;")
            items[key] = led
            layout.addWidget(led)
            layout.addWidget(QLabel(key))
        return layout
    
    def change_mode(self, mode):
        if mode == "Normal":
            color = "green"
            message = "Cambiando a modo Normal: Encendido todos los sensores y subsistemas."
        elif mode == "Apagado":
            color = "red"
            message = "Cambiando a modo Apagado: Apagado todos los sensores y subsistemas."
        else:
            color = "red"
            message = "Cambiando a modo Emergencia: Estado desconocido."
        
        for led in self.subsystems.values():
            led.setStyleSheet(f"background-color: {color}; border-radius: 10px;")
        for led in self.sensors.values():
            led.setStyleSheet(f"background-color: {color}; border-radius: 10px;")
        
        self.command_box.append(message)
        self.mode_label.setText(f"Modo: {mode}")


app = QApplication(sys.argv)
window = CubeSatInterface()
window.show()
sys.exit(app.exec())