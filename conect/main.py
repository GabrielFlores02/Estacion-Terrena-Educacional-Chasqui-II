# ESP32 (archivo main.py)
from machine import Pin, I2C, UART
import time
import json

# Configurar UART
uart = UART(2, baudrate=115200)  # UART2 en ESP32

def read_sensors():
    # Simular lecturas de sensores - reemplazar con tus lecturas reales
    return {
        "accel": {
            "x": 0,  # Lectura real del acelerómetro
            "y": 0,
            "z": 0
        },
        "gyro": {
            "roll": 0,  # Lectura real del giroscopio
            "pitch": 0,
            "yaw": 0
        },
        "gps": {
            "lat": -12.0464,  # Lectura real del GPS
            "lon": -77.0428
        },
        "uv_index": 0,  # Lectura real del sensor UV
        "temperature": 0  # Lectura real del sensor de temperatura
    }

def main():
    while True:
        try:
            # Leer datos de sensores
            data = read_sensors()
            # Convertir a JSON y enviar
            message = json.dumps(data) + '\n'  # Añadir newline como delimitador
            uart.write(message.encode())
            time.sleep(1)
        except Exception as e:
            print("Error:", e)
            time.sleep(1)

if __name__ == "__main__":
    main()
