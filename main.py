import sys
import folium
import os
import random
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QWidget, QFrame, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer, Qt
from PyQt5.QtGui import QPixmap, QPalette, QBrush
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('sensor_data.db')
        self.cursor = self.conn.cursor()
        self.create_table()
        print("Base de datos iniciada correctamente")

    def create_table(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            accel_x REAL,
            accel_y REAL,
            accel_z REAL,
            gyro_roll REAL,
            gyro_pitch REAL,
            gyro_yaw REAL,
            gps_lat REAL,
            gps_lon REAL,
            uv_index REAL,
            temperature REAL
        )
        ''')
        self.conn.commit()

    def insert_data(self, data):
        try:
            self.cursor.execute('''
            INSERT INTO sensor_data (
                timestamp, accel_x, accel_y, accel_z, 
                gyro_roll, gyro_pitch, gyro_yaw,
                gps_lat, gps_lon, uv_index, temperature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', data)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error al insertar datos: {e}")

    def close(self):
        self.conn.close()
        print("Conexión a la base de datos cerrada")

class LiveGraph(FigureCanvas):
    def __init__(self, title, xlabel, ylabel):
        self.fig = Figure(figsize=(5, 4))
        self.ax = self.fig.add_subplot(111)
        self.title = title  # Guardar el título como atributo
        self.xlabel = xlabel  # Guardar el xlabel como atributo
        self.ylabel = ylabel  # Guardar el ylabel como atributo
        self.ax.set_title(title, fontsize=10, pad=10)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.data_x = []
        self.data_y = []
        self.counter = 0  # Contador para el eje x
        super().__init__(self.fig)
        self.fig.tight_layout()

    def update_graph(self, new_y):
        self.counter += 1
        self.data_y.append(new_y)
        
        # Mantener solo los últimos 20 valores
        if len(self.data_y) > 20:
            self.data_y.pop(0)
        
        self.ax.clear()
        # Crear array de x basado en el contador
        x_values = np.arange(self.counter - len(self.data_y) + 1, self.counter + 1)
        self.ax.plot(x_values, self.data_y, '-o')
        
        # Restablecer los títulos usando los atributos almacenados
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        self.ax.set_title(self.title, fontsize=10, pad=10)
        self.ax.grid(True)
        
        # Ajustar el rango del eje x para mostrar siempre los últimos 20 valores
        if self.counter > 20:
            self.ax.set_xlim(self.counter - 19, self.counter + 1)
        
        self.fig.tight_layout()
        self.draw()

class MapaFolium(QWidget):
    def __init__(self, lat, lon):
        super().__init__()
        self.lat = lat
        self.lon = lon

        self.mapa = folium.Map(location=[lat, lon], zoom_start=15)
        self.marker = folium.Marker([lat, lon], popup="Ubicación seleccionada")
        self.marker.add_to(self.mapa)

        self.mapa_file = os.path.abspath("mapa.html")
        self.mapa.save(self.mapa_file)

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl.fromLocalFile(self.mapa_file))

        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        self.setLayout(layout)

    def update_marker(self, lat, lon):
        self.lat = lat
        self.lon = lon
        self.mapa = folium.Map(location=[lat, lon], zoom_start=15)
        folium.Marker([lat, lon], popup="Ubicación actual").add_to(self.mapa)
        self.mapa.save(self.mapa_file)
        self.browser.reload()

class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interfaz de Sensores")
        self.setGeometry(100, 100, 1200, 800)
        
        # Inicializar base de datos
        self.db = Database()
        
        # Configurar UI
        self.setup_ui()
        
        # Timer para actualizar datos
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)  # Actualización cada 1 segundo

    def setup_ui(self):
        palette = QPalette()
        background_img = QPixmap("assets/fondo3.png")
        scaled_img = background_img.scaled(self.size(), Qt.IgnoreAspectRatio)
        palette.setBrush(QPalette.Window, QBrush(scaled_img))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # Layout principal
        main_layout = QVBoxLayout()
        
        # Layout para logos
        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(20)
        
        # Logo universidad
        uni_logo = QLabel()
        uni_pixmap = QPixmap("assets/logo_uni.png")
        uni_logo.setPixmap(uni_pixmap.scaled(100, 100, Qt.KeepAspectRatio))
        logo_layout.addWidget(uni_logo)
        
        # Título central
        self.title = QLabel()
        self.title.setText("<h1 style='color:white;'>CubeSat Interface</h1>")
        self.title.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(self.title, stretch=1)
        
        # Logo proyecto
        project_logo = QLabel()
        project_pixmap = QPixmap("assets/logo_chasqui_1.jpg")
        project_logo.setPixmap(project_pixmap.scaled(100, 100, Qt.KeepAspectRatio))
        logo_layout.addWidget(project_logo)

        main_layout.addLayout(logo_layout)

        # Botón para abrir el visualizador de base de datos
        database_btn_layout = QHBoxLayout()
        self.database_viewer_btn = QPushButton("Ver Datos Históricos")
        self.database_viewer_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 100, 150, 180);
                color: white;
                border: 1px solid white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 130, 180, 180);
            }
        """)
        self.database_viewer_btn.clicked.connect(self.open_database_viewer)
        database_btn_layout.addStretch()
        database_btn_layout.addWidget(self.database_viewer_btn)
        database_btn_layout.addStretch()
        main_layout.addLayout(database_btn_layout)

        # Layout superior
        top_layout = QGridLayout()
        top_layout.setSpacing(15)

        # Frame para datos del acelerómetro
        accel_frame = QFrame()
        accel_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        accel_frame.setStyleSheet("QFrame { background-color: rgba(0, 0, 0, 100); border: 1px solid white; }")
        accel_layout = QVBoxLayout()
        
        # Labels para acelerómetro
        self.label_x = QLabel("X: ...")
        self.label_y = QLabel("Y: ...")
        self.label_z = QLabel("Z: ...")
        for label in [self.label_x, self.label_y, self.label_z]:
            label.setStyleSheet("QLabel { color: white; font-weight: bold; min-width: 150px; }")
            label.setAlignment(Qt.AlignLeft)
            accel_layout.addWidget(label)
        accel_frame.setLayout(accel_layout)
        top_layout.addWidget(accel_frame, 0, 0)

        # Frame para orientación
        orient_frame = QFrame()
        orient_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        orient_frame.setStyleSheet("QFrame { background-color: rgba(0, 0, 0, 100); border: 1px solid white; }")
        orient_layout = QVBoxLayout()

        # Labels de orientación
        self.label_roll = QLabel("Roll: ...")
        self.label_pitch = QLabel("Pitch: ...")
        self.label_yaw = QLabel("Yaw: ...")
        for label in [self.label_roll, self.label_pitch, self.label_yaw]:
            label.setStyleSheet("QLabel { color: white; font-weight: bold; min-width: 150px; }")
            label.setAlignment(Qt.AlignLeft)
            orient_layout.addWidget(label)
        orient_frame.setLayout(orient_layout)
        top_layout.addWidget(orient_frame, 0, 1)

        # Frame para GPS
        gps_frame = QFrame()
        gps_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        gps_frame.setStyleSheet("QFrame { background-color: rgba(0, 0, 0, 100); border: 1px solid white; }")
        gps_layout = QVBoxLayout()

        # Labels GPS
        self.label_lat = QLabel("Lat: ...")
        self.label_lon = QLabel("Lon: ...")
        for label in [self.label_lat, self.label_lon]:
            label.setStyleSheet("QLabel { color: white; font-weight: bold; min-width: 150px; }")
            label.setAlignment(Qt.AlignLeft)
            gps_layout.addWidget(label)
        gps_frame.setLayout(gps_layout)
        top_layout.addWidget(gps_frame, 0, 2)

        # Mapa
        self.map_widget = MapaFolium(lat=-12.0464, lon=-77.0428)
        top_layout.addWidget(self.map_widget, 0, 3, 3, 1)

        # Crear línea divisoria
        line_divisor = QFrame()
        line_divisor.setFrameShape(QFrame.HLine)
        line_divisor.setFrameShadow(QFrame.Sunken)
        line_divisor.setStyleSheet("QFrame { background-color: white; }")

        # Layout inferior con gráficos
        bottom_layout = QHBoxLayout()
        self.uv_graph = LiveGraph(
            "Índice de Radiación UV", 
            "Tiempo (s)", 
            "Índice UV"
        )
        self.temp_graph = LiveGraph(
            "Temperatura del Sistema",
            "Tiempo (s)",
            "Temperatura (°C)"
        )
        bottom_layout.addWidget(self.uv_graph)
        bottom_layout.addWidget(self.temp_graph)

        # Ensamblar layouts
        main_layout.addLayout(top_layout)
        main_layout.addWidget(line_divisor)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def open_database_viewer(self):
        from database_viewer import DatabaseViewer
        viewer = DatabaseViewer(self)
        viewer.exec_()

    def update_data(self):
        # Simular datos
        lat, lon = -12.0464 + random.uniform(-0.001, 0.001), -77.0428 + random.uniform(-0.001, 0.001)
        x, y, z = random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-10, 10)
        roll, pitch, yaw = random.uniform(-180, 180), random.uniform(-180, 180), random.uniform(-180, 180)
        uv = random.uniform(0, 11)
        temp = random.uniform(15, 40)

        # Guardar en la base de datos
        data = (
            datetime.now(),  # timestamp
            x, y, z,        # acelerómetro
            roll, pitch, yaw,  # giroscopio
            lat, lon,          # GPS
            uv, temp           # sensores
        )
        self.db.insert_data(data)

        # Actualizar labels
        self.label_x.setText(f"X: {x:.2f} m/s²")
        self.label_y.setText(f"Y: {y:.2f} m/s²")
        self.label_z.setText(f"Z: {z:.2f} m/s²")
        self.label_roll.setText(f"Roll: {roll:.2f}°")
        self.label_pitch.setText(f"Pitch: {pitch:.2f}°")
        self.label_yaw.setText(f"Yaw: {yaw:.2f}°")
        self.label_lat.setText(f"Lat: {lat:.5f}°")
        self.label_lon.setText(f"Lon: {lon:.5f}°")

        # Actualizar gráficos
        self.uv_graph.update_graph(uv)
        self.temp_graph.update_graph(temp)

        # Actualizar marcador en el mapa
        self.map_widget.update_marker(lat, lon)

    def closeEvent(self, event):
        # Cerrar la conexión a la base de datos al cerrar la aplicación
        self.db.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MainApp()
    ventana.show()
    sys.exit(app.exec_())