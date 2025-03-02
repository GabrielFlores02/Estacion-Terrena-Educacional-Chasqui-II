import sys
import pandas as pd
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                            QWidget, QFrame, QPushButton, QDateTimeEdit, QTableView,
                            QFileDialog, QComboBox, QGroupBox, QStatusBar, QMessageBox,
                            QCheckBox)
from PyQt5.QtCore import Qt, QDateTime, QSortFilterProxyModel, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import sqlite3
from datetime import datetime, timedelta

class DatabaseViewer(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visualizador de Datos Históricos")
        self.setGeometry(100, 100, 1000, 700)
        self.parent = parent
        
        # Variable para controlar la actualización en tiempo real
        self.real_time_enabled = False
        self.last_id = 0  # Para rastrear el último ID recuperado
        
        # Timer para actualización en tiempo real
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_real_time_data)
        
        # Configurar UI
        self.setup_ui()
        
        # Cargar datos iniciales (los últimos 24 horas)
        self.load_initial_data()

    def setup_ui(self):
        # Layout principal
        main_layout = QVBoxLayout()
        
        # ---- Sección de Filtros ----
        filter_group = QGroupBox("Filtros")
        filter_layout = QGridLayout()
        
        # Modo tiempo real
        self.real_time_checkbox = QCheckBox("Mostrar en tiempo real")
        self.real_time_checkbox.toggled.connect(self.toggle_real_time)
        filter_layout.addWidget(self.real_time_checkbox, 0, 0, 1, 2)
        
        # Filtro por fecha de inicio
        start_label = QLabel("Fecha inicio:")
        self.start_date = QDateTimeEdit(QDateTime.currentDateTime().addDays(-1))
        self.start_date.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        self.start_date.setCalendarPopup(True)
        filter_layout.addWidget(start_label, 1, 0)
        filter_layout.addWidget(self.start_date, 1, 1)
        
        # Filtro por fecha final
        end_label = QLabel("Fecha fin:")
        self.end_date = QDateTimeEdit(QDateTime.currentDateTime())
        self.end_date.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        self.end_date.setCalendarPopup(True)
        filter_layout.addWidget(end_label, 1, 2)
        filter_layout.addWidget(self.end_date, 1, 3)
        
        # Presets de tiempo
        preset_label = QLabel("Periodo:")
        self.time_preset = QComboBox()
        self.time_preset.addItems(["Personalizado", "Última hora", "Últimas 24 horas", 
                                  "Última semana", "Último mes"])
        self.time_preset.currentIndexChanged.connect(self.apply_time_preset)
        filter_layout.addWidget(preset_label, 2, 0)
        filter_layout.addWidget(self.time_preset, 2, 1)
        
        # Botón para aplicar filtros
        self.apply_btn = QPushButton("Aplicar Filtros")
        self.apply_btn.clicked.connect(self.apply_filters)
        filter_layout.addWidget(self.apply_btn, 2, 3)
        
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)
        
        # ---- Tabla de Datos ----
        table_group = QGroupBox("Datos del Sensor")
        table_layout = QVBoxLayout()
        
        # Crear modelo de tabla y vista
        self.model = QStandardItemModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        
        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSortingEnabled(True)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        
        table_layout.addWidget(self.table_view)
        
        # Información de registros
        self.records_info = QLabel("Registros: 0")
        table_layout.addWidget(self.records_info)
        
        table_group.setLayout(table_layout)
        main_layout.addWidget(table_group)
        
        # ---- Botones de Acción ----
        btn_layout = QHBoxLayout()
        
        # Botón para exportar a CSV
        self.export_csv_btn = QPushButton("Exportar a CSV")
        self.export_csv_btn.clicked.connect(lambda: self.export_data("csv"))
        btn_layout.addWidget(self.export_csv_btn)
        
        # Botón para exportar a Excel
        self.export_excel_btn = QPushButton("Exportar a Excel")
        self.export_excel_btn.clicked.connect(lambda: self.export_data("excel"))
        btn_layout.addWidget(self.export_excel_btn)
        
        # Botón para cerrar
        self.close_btn = QPushButton("Cerrar")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(btn_layout)
        
        # Barra de estado
        self.status_bar = QStatusBar()
        main_layout.addWidget(self.status_bar)
        
        self.setLayout(main_layout)
        
        # Configurar encabezados de la tabla
        headers = ["ID", "Fecha y Hora", "Acel X", "Acel Y", "Acel Z", 
                   "Roll", "Pitch", "Yaw", "Latitud", "Longitud", 
                   "Índice UV", "Temperatura"]
        self.model.setHorizontalHeaderLabels(headers)

    def load_initial_data(self):
        """Carga los datos de las últimas 24 horas"""
        self.time_preset.setCurrentIndex(2)  # "Últimas 24 horas"
        self.apply_filters()

    def toggle_real_time(self, enabled):
        """Activa o desactiva la actualización en tiempo real"""
        self.real_time_enabled = enabled
        
        # Activar/desactivar elementos de filtro según el modo
        self.start_date.setEnabled(not enabled)
        self.end_date.setEnabled(not enabled)
        self.time_preset.setEnabled(not enabled)
        self.apply_btn.setEnabled(not enabled)
        
        if enabled:
            # Obtener el último ID para empezar a seguir desde ahí
            try:
                conn = sqlite3.connect('sensor_data.db')
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(id) FROM sensor_data")
                max_id = cursor.fetchone()[0]
                if max_id:
                    self.last_id = max_id
                conn.close()
                
                # Limpiar la tabla actual
                self.model.removeRows(0, self.model.rowCount())
                self.records_info.setText("Registros: 0")
                
                # Iniciar timer para actualizaciones en tiempo real (cada 1 segundo)
                self.update_timer.start(1000)
                self.status_bar.showMessage("Modo tiempo real activado")
            except Exception as e:
                self.status_bar.showMessage(f"Error al iniciar modo tiempo real: {str(e)}")
                self.real_time_checkbox.setChecked(False)
        else:
            # Detener el timer
            self.update_timer.stop()
            self.status_bar.showMessage("Modo tiempo real desactivado")

    def update_real_time_data(self):
        """Actualiza la tabla con los nuevos datos desde el último ID conocido"""
        try:
            conn = sqlite3.connect('sensor_data.db')
            
            # Consulta para obtener solo los nuevos registros
            query = f"""
            SELECT id, timestamp, accel_x, accel_y, accel_z, 
                   gyro_roll, gyro_pitch, gyro_yaw,
                   gps_lat, gps_lon, uv_index, temperature
            FROM sensor_data
            WHERE id > {self.last_id}
            ORDER BY id ASC
            """
            
            # Obtener datos como DataFrame
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df.empty:
                # Actualizar el último ID conocido
                self.last_id = df['id'].max()
                
                # Añadir nuevos datos al modelo (al principio para mostrar los más recientes primero)
                for i, row in df.iterrows():
                    items = []
                    for value in row:
                        # Formatear valores numéricos con 2 decimales
                        if isinstance(value, (int, float)) and not isinstance(value, bool):
                            if isinstance(value, int):
                                item = QStandardItem(str(value))
                            else:
                                item = QStandardItem(f"{value:.2f}")
                        else:
                            item = QStandardItem(str(value))
                        items.append(item)
                    self.model.insertRow(0, items)  # Insertar al principio
                
                # Limitar a 1000 filas para evitar consumo excesivo de memoria
                if self.model.rowCount() > 1000:
                    self.model.removeRows(1000, self.model.rowCount() - 1000)
                
                # Actualizar información de registros
                self.records_info.setText(f"Registros: {self.model.rowCount()} (mostrando los últimos 1000)")
                
                # Ajustar ancho de columnas automáticamente
                self.table_view.resizeColumnsToContents()
                
        except Exception as e:
            self.status_bar.showMessage(f"Error al actualizar datos en tiempo real: {str(e)}")

    def apply_time_preset(self):
        """Aplica preajustes de tiempo a los selectores de fecha"""
        current_time = QDateTime.currentDateTime()
        preset = self.time_preset.currentText()
        
        if preset == "Última hora":
            self.start_date.setDateTime(current_time.addSecs(-3600))
            self.end_date.setDateTime(current_time)
        elif preset == "Últimas 24 horas":
            self.start_date.setDateTime(current_time.addDays(-1))
            self.end_date.setDateTime(current_time)
        elif preset == "Última semana":
            self.start_date.setDateTime(current_time.addDays(-7))
            self.end_date.setDateTime(current_time)
        elif preset == "Último mes":
            self.start_date.setDateTime(current_time.addMonths(-1))
            self.end_date.setDateTime(current_time)
        # Si es "Personalizado" no hacemos nada

    def apply_filters(self):
        """Aplica los filtros y actualiza la tabla de datos"""
        # Desactivar actualización en tiempo real si está activa
        if self.real_time_enabled:
            self.real_time_checkbox.setChecked(False)
        
        start_datetime = self.start_date.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        end_datetime = self.end_date.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        
        try:
            # Conectar a la base de datos
            conn = sqlite3.connect('sensor_data.db')
            
            # Consulta SQL con filtros
            query = f"""
            SELECT id, timestamp, accel_x, accel_y, accel_z, 
                   gyro_roll, gyro_pitch, gyro_yaw,
                   gps_lat, gps_lon, uv_index, temperature
            FROM sensor_data
            WHERE timestamp BETWEEN '{start_datetime}' AND '{end_datetime}'
            ORDER BY timestamp DESC
            """
            
            # Obtener datos como DataFrame
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Actualizar el modelo de la tabla
            self.update_table_model(df)
            
            # Actualizar información de registros
            self.records_info.setText(f"Registros: {len(df)}")
            self.status_bar.showMessage(f"Datos cargados: {len(df)} registros")
            
        except Exception as e:
            self.status_bar.showMessage(f"Error al cargar datos: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error al consultar la base de datos: {str(e)}")

    def update_table_model(self, df):
        """Actualiza el modelo de la tabla con los datos del DataFrame"""
        # Limpiar modelo actual
        self.model.removeRows(0, self.model.rowCount())
        
        # Añadir filas
        for i, row in df.iterrows():
            items = []
            for value in row:
                # Formatear valores numéricos con 2 decimales
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    if isinstance(value, int):
                        item = QStandardItem(str(value))
                    else:
                        item = QStandardItem(f"{value:.2f}")
                else:
                    item = QStandardItem(str(value))
                items.append(item)
            self.model.appendRow(items)
            
        # Ajustar ancho de columnas automáticamente
        self.table_view.resizeColumnsToContents()

    def export_data(self, format_type):
        """Exporta los datos filtrados a un archivo CSV o Excel"""
        # Asegurarse de que hay datos para exportar
        if self.model.rowCount() == 0:
            self.status_bar.showMessage("No hay datos para exportar")
            return
            
        # Solicitar ubicación y nombre de archivo
        options = QFileDialog.Options()
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == "csv":
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Guardar como CSV", f"datos_sensores_{current_time}.csv",
                "Archivos CSV (*.csv)", options=options
            )
            if not file_name:
                return
                
            # Convertir modelo a DataFrame
            df = self.model_to_dataframe()
            
            # Guardar como CSV
            try:
                df.to_csv(file_name, index=False)
                self.status_bar.showMessage(f"Datos exportados a {file_name}")
            except Exception as e:
                self.status_bar.showMessage(f"Error al exportar: {str(e)}")
                
        elif format_type == "excel":
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Guardar como Excel", f"datos_sensores_{current_time}.xlsx",
                "Archivos Excel (*.xlsx)", options=options
            )
            if not file_name:
                return
                
            # Convertir modelo a DataFrame
            df = self.model_to_dataframe()
            
            # Guardar como Excel
            try:
                df.to_excel(file_name, index=False)
                self.status_bar.showMessage(f"Datos exportados a {file_name}")
            except Exception as e:
                self.status_bar.showMessage(f"Error al exportar: {str(e)}")

    def model_to_dataframe(self):
        """Convierte el modelo de tabla a un DataFrame de pandas"""
        # Obtener encabezados
        headers = []
        for i in range(self.model.columnCount()):
            headers.append(self.model.headerData(i, Qt.Horizontal))
            
        # Obtener datos
        data = []
        for row in range(self.model.rowCount()):
            row_data = []
            for col in range(self.model.columnCount()):
                item = self.model.item(row, col)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            data.append(row_data)
            
        # Crear DataFrame
        return pd.DataFrame(data, columns=headers)
        
    def closeEvent(self, event):
        """Se ejecuta cuando se cierra la ventana"""
        # Detener el timer si está activo
        if self.update_timer.isActive():
            self.update_timer.stop()
        event.accept()