import serial
import json
from datetime import datetime
import serial.tools.list_ports

class SerialDataClient:
    def __init__(self, baudrate=115200):
        self.serial = None
        self.baudrate = baudrate
        self.data_callback = None
        self.running = False
        
    def list_ports(self):
        """Lista todos los puertos seriales disponibles"""
        ports = serial.tools.list_ports.comports()
        return [(port.device, port.description) for port in ports]
        
    def connect(self, port):
        """Conecta al puerto serial especificado"""
        try:
            self.serial = serial.Serial(port, self.baudrate)
            print(f"Conectado a {port}")
            return True
        except Exception as e:
            print(f"Error al conectar: {e}")
            return False
            
    def set_callback(self, callback):
        """Establece la función callback que procesará los datos recibidos"""
        self.data_callback = callback
        
    def start_reading(self):
        """Inicia la lectura de datos"""
        if not self.serial:
            raise Exception("No hay conexión serial establecida")
        
        self.running = True
        while self.running:
            if self.serial.in_waiting:
                try:
                    line = self.serial.readline().decode().strip()
                    data = json.loads(line)
                    if self.data_callback:
                        self.data_callback(data)
                except Exception as e:
                    print(f"Error leyendo datos: {e}")
                    
    def stop(self):
        """Detiene la lectura y cierra la conexión"""
        self.running = False
        if self.serial:
            self.serial.close()