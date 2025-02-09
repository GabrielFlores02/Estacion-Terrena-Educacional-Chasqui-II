#Cambios en el Main de la App

class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interfaz de Sensores")
        self.setGeometry(100, 100, 1200, 800)
        
        # Inicializar base de datos
        self.db = Database()
        
        # Inicializar cliente serial
        self.serial_client = SerialDataClient()
        
        # Encontrar y conectar al ESP32
        ports = self.serial_client.list_ports()
        # Buscar un puerto que contenga "USB" o "CP210x" (común en ESP32)
        esp32_port = next((port for port, desc in ports if "USB" in desc or "CP210x" in desc), None)
        
        if esp32_port:
            if self.serial_client.connect(esp32_port):
                self.serial_client.set_callback(self.process_sensor_data)
                # Iniciar lectura en un hilo separado
                from threading import Thread
                self.serial_thread = Thread(target=self.serial_client.start_reading)
                self.serial_thread.daemon = True
                self.serial_thread.start()
        
        # Configurar UI
        self.setup_ui()
        
    def process_sensor_data(self, data):
        """Procesa los datos recibidos del ESP32"""
        # Extraer datos
        accel = data['accel']
        gyro = data['gyro']
        gps = data['gps']
        
        # Guardar en la base de datos
        db_data = (
            datetime.now(),
            accel['x'], accel['y'], accel['z'],
            gyro['roll'], gyro['pitch'], gyro['yaw'],
            gps['lat'], gps['lon'],
            data['uv_index'], data['temperature']
        )
        self.db.insert_data(db_data)
        
        # Actualizar UI
        self.label_x.setText(f"X: {accel['x']:.2f} m/s²")
        self.label_y.setText(f"Y: {accel['y']:.2f} m/s²")
        self.label_z.setText(f"Z: {accel['z']:.2f} m/s²")
        self.label_roll.setText(f"Roll: {gyro['roll']:.2f}°")
        self.label_pitch.setText(f"Pitch: {gyro['pitch']:.2f}°")
        self.label_yaw.setText(f"Yaw: {gyro['yaw']:.2f}°")
        self.label_lat.setText(f"Lat: {gps['lat']:.5f}°")
        self.label_lon.setText(f"Lon: {gps['lon']:.5f}°")
        
        # Actualizar gráficos
        self.uv_graph.update_graph(data['uv_index'])
        self.temp_graph.update_graph(data['temperature'])
        
        # Actualizar mapa
        self.map_widget.update_marker(gps['lat'], gps['lon'])
        
    def closeEvent(self, event):
        if hasattr(self, 'serial_client'):
            self.serial_client.stop()
        self.db.close()
        event.accept()