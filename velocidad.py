import sys
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QComboBox, QTextEdit, QGroupBox, QGridLayout,
                             QFrame, QMessageBox, QTabWidget, QTableWidget,
                             QTableWidgetItem, QHeaderView, QSplitter,
                             QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor

class CalibrationPlot(FigureCanvas):
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        self.axes = self.fig.add_subplot(111)
        self.clear_plot()
        
    def clear_plot(self):
        """Limpia el gráfico"""
        self.axes.clear()
        self.axes.set_xlabel('Velocidad Patrón (m/s)', fontsize=12)
        self.axes.set_ylabel('Error (m/s)', fontsize=12)
        self.axes.set_title('Error vs Velocidad - Calibración de Velocímetro', fontsize=14, fontweight='bold')
        self.axes.grid(True, alpha=0.3)
        self.axes.axhline(y=0, color='k', linestyle='-', alpha=0.5)
        self.draw()
    
    def update_plot(self, velocity_patron, errors, statistics):
        """Actualiza el gráfico con los datos de calibración"""
        self.axes.clear()
        
        # Configurar el gráfico
        self.axes.set_xlabel('Velocidad Patrón (m/s)', fontsize=12)
        self.axes.set_ylabel('Error (m/s)', fontsize=12)
        self.axes.set_title('Error vs Velocidad - Calibración de Velocímetro', fontsize=14, fontweight='bold')
        self.axes.grid(True, alpha=0.3)
        
        # Línea de error cero
        self.axes.axhline(y=0, color='k', linestyle='-', alpha=0.5, label='Error = 0')
        
        # Puntos de error en rojo
        self.axes.scatter(velocity_patron, errors, color='red', s=80, alpha=0.8, 
                         edgecolors='darkred', linewidth=1, label='Puntos de medición')
        
        # Línea de tendencia
        if len(velocity_patron) > 1:
            z = np.polyfit(velocity_patron, errors, 1)
            p = np.poly1d(z)
            x_trend = np.linspace(min(velocity_patron), max(velocity_patron), 100)
            self.axes.plot(x_trend, p(x_trend), 'b--', alpha=0.7, 
                          label=f'Tendencia: y = {z[0]:.4f}x + {z[1]:.4f}')
        
        # Bandas de incertidumbre (±2σ)
        if statistics['std_error'] > 0:
            mean_error = statistics['mean_error']
            std_error = statistics['std_error']
            
            self.axes.axhline(y=mean_error + 2*std_error, color='orange', 
                             linestyle=':', alpha=0.7, label='+2σ')
            self.axes.axhline(y=mean_error - 2*std_error, color='orange', 
                             linestyle=':', alpha=0.7, label='-2σ')
            
            # Sombreado de incertidumbre
            x_range = self.axes.get_xlim()
            self.axes.fill_between(x_range, mean_error - 2*std_error, 
                                  mean_error + 2*std_error, alpha=0.1, color='orange')
        
        # Estadísticas en el gráfico
        stats_text = f"""Estadísticas:
Error medio: {statistics['mean_error']:.4f} m/s
Desv. estándar: {statistics['std_error']:.4f} m/s
Error máximo: {statistics['max_error']:.4f} m/s
Error mínimo: {statistics['min_error']:.4f} m/s
Incertidumbre (2σ): ±{2*statistics['std_error']:.4f} m/s"""
        
        self.axes.text(0.02, 0.98, stats_text, transform=self.axes.transAxes,
                      verticalalignment='top', bbox=dict(boxstyle='round', 
                      facecolor='wheat', alpha=0.8), fontsize=9)
        
        self.axes.legend(loc='upper right')
        self.draw()

class PipeVelocityCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.calibration_data = []
        self.init_ui()
        
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        self.setWindowTitle("Calculadora de Velocidad y Sistema de Calibración")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 12px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
                font-size: 11px;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e1e1e1;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)
        
        # Widget central con pestañas
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Título principal
        title = QLabel("Sistema de Cálculo de Velocidad y Calibración de Velocímetros")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #333; margin: 10px;")
        main_layout.addWidget(title)
        
        # Pestañas
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Pestaña 1: Calculadora básica
        self.setup_calculator_tab()
        
        # Pestaña 2: Calibración
        self.setup_calibration_tab()
        
    def setup_calculator_tab(self):
        """Configura la pestaña de calculadora básica"""
        calc_widget = QWidget()
        calc_layout = QVBoxLayout()
        
        # Grupo de entrada de datos
        input_group = QGroupBox("Datos de Entrada")
        input_layout = QGridLayout()
        
        # Caudal
        input_layout.addWidget(QLabel("Caudal:"), 0, 0)
        self.caudal_input = QLineEdit()
        self.caudal_input.setPlaceholderText("Ingrese el caudal")
        input_layout.addWidget(self.caudal_input, 0, 1)
        
        self.caudal_units = QComboBox()
        self.caudal_units.addItems([
            "m³/h (metros cúbicos por hora)",
            "L/h (litros por hora)", 
            "L/min (litros por minuto)",
            "L/s (litros por segundo)",
            "m³/s (metros cúbicos por segundo)",
            "GPM (galones por minuto)",
            "CFM (pies cúbicos por minuto)"
        ])
        input_layout.addWidget(self.caudal_units, 0, 2)
        
        # Diámetro exterior
        input_layout.addWidget(QLabel("Diámetro exterior (mm):"), 1, 0)
        self.diametro_input = QLineEdit()
        self.diametro_input.setPlaceholderText("Diámetro exterior en mm")
        input_layout.addWidget(self.diametro_input, 1, 1, 1, 2)
        
        # Espesor
        input_layout.addWidget(QLabel("Espesor de pared (mm):"), 2, 0)
        self.espesor_input = QLineEdit()
        self.espesor_input.setPlaceholderText("Espesor de la pared en mm")
        input_layout.addWidget(self.espesor_input, 2, 1, 1, 2)
        
        input_group.setLayout(input_layout)
        calc_layout.addWidget(input_group)
        
        # Botones
        button_layout = QHBoxLayout()
        
        self.calculate_btn = QPushButton("Calcular Velocidad")
        self.calculate_btn.clicked.connect(self.calculate_velocity)
        button_layout.addWidget(self.calculate_btn)
        
        self.clear_btn = QPushButton("Limpiar")
        self.clear_btn.setStyleSheet("background-color: #f44336;")
        self.clear_btn.clicked.connect(self.clear_fields)
        button_layout.addWidget(self.clear_btn)
        
        calc_layout.addLayout(button_layout)
        
        # Resultados
        results_group = QGroupBox("Resultados")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(150)
        self.results_text.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        calc_layout.addWidget(results_group)
        
        # Información de fórmulas
        formula_group = QGroupBox("Fórmulas Utilizadas")
        formula_layout = QVBoxLayout()
        
        formula_text = QLabel("""
        • Diámetro interior: Di = De - 2×espesor
        • Área de flujo: A = π × (Di/2)²
        • Velocidad: v = Q / A
        
        Donde: De=Diámetro exterior, Di=Diámetro interior, Q=Caudal, A=Área transversal, v=Velocidad del fluido
        """)
        formula_text.setStyleSheet("color: #555; font-size: 10px;")
        formula_layout.addWidget(formula_text)
        
        formula_group.setLayout(formula_layout)
        calc_layout.addWidget(formula_group)
        
        calc_widget.setLayout(calc_layout)
        self.tab_widget.addTab(calc_widget, "Calculadora de Velocidad")
    
    def setup_calibration_tab(self):
        """Configura la pestaña de calibración"""
        calib_widget = QWidget()
        calib_layout = QHBoxLayout()
        
        # Panel izquierdo: Controles
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setMaximumWidth(400)
        
        # Configuración de tubería para calibración
        pipe_group = QGroupBox("Configuración de Tubería")
        pipe_layout = QGridLayout()
        
        pipe_layout.addWidget(QLabel("Diámetro exterior (mm):"), 0, 0)
        self.calib_diametro = QLineEdit()
        self.calib_diametro.setPlaceholderText("Diámetro exterior")
        pipe_layout.addWidget(self.calib_diametro, 0, 1)
        
        pipe_layout.addWidget(QLabel("Espesor (mm):"), 1, 0)
        self.calib_espesor = QLineEdit()
        self.calib_espesor.setPlaceholderText("Espesor de pared")
        pipe_layout.addWidget(self.calib_espesor, 1, 1)
        
        pipe_group.setLayout(pipe_layout)
        left_layout.addWidget(pipe_group)
        
        # Entrada de datos de calibración
        data_group = QGroupBox("Datos de Calibración")
        data_layout = QGridLayout()
        
        data_layout.addWidget(QLabel("Caudal patrón:"), 0, 0)
        self.calib_caudal = QLineEdit()
        self.calib_caudal.setPlaceholderText("Caudal del patrón")
        data_layout.addWidget(self.calib_caudal, 0, 1)
        
        self.calib_caudal_units = QComboBox()
        self.calib_caudal_units.addItems([
            "m³/h", "L/h", "L/min", "L/s", "m³/s", "GPM", "CFM"
        ])
        data_layout.addWidget(self.calib_caudal_units, 0, 2)
        
        data_layout.addWidget(QLabel("Velocidad equipo (m/s):"), 1, 0)
        self.calib_velocidad_equipo = QLineEdit()
        self.calib_velocidad_equipo.setPlaceholderText("Lectura del equipo a calibrar")
        data_layout.addWidget(self.calib_velocidad_equipo, 1, 1, 1, 2)
        
        data_group.setLayout(data_layout)
        left_layout.addWidget(data_group)
        
        # Botones de calibración
        calib_button_layout = QVBoxLayout()
        
        self.add_point_btn = QPushButton("Agregar Punto")
        self.add_point_btn.clicked.connect(self.add_calibration_point)
        calib_button_layout.addWidget(self.add_point_btn)
        
        self.clear_calib_btn = QPushButton("Limpiar Calibración")
        self.clear_calib_btn.setStyleSheet("background-color: #ff9800;")
        self.clear_calib_btn.clicked.connect(self.clear_calibration)
        calib_button_layout.addWidget(self.clear_calib_btn)
        
        self.export_btn = QPushButton("Exportar Resultados")
        self.export_btn.setStyleSheet("background-color: #2196F3;")
        self.export_btn.clicked.connect(self.export_results)
        calib_button_layout.addWidget(self.export_btn)
        
        left_layout.addLayout(calib_button_layout)
        
        # Tabla de datos
        table_group = QGroupBox("Datos de Calibración")
        table_layout = QVBoxLayout()
        
        self.calib_table = QTableWidget()
        self.calib_table.setColumnCount(4)
        self.calib_table.setHorizontalHeaderLabels([
            "Punto", "V. Patrón (m/s)", "V. Equipo (m/s)", "Error (m/s)"
        ])
        self.calib_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.calib_table)
        
        table_group.setLayout(table_layout)
        left_layout.addWidget(table_group)
        
        # Estadísticas
        stats_group = QGroupBox("Estadísticas de Calibración")
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(120)
        self.stats_text.setStyleSheet("background-color: #f9f9f9; font-family: monospace;")
        stats_layout = QVBoxLayout()
        stats_layout.addWidget(self.stats_text)
        stats_group.setLayout(stats_layout)
        left_layout.addWidget(stats_group)
        
        left_panel.setLayout(left_layout)
        
        # Panel derecho: Gráfico
        self.plot_widget = CalibrationPlot()
        
        # Splitter para dividir paneles
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.plot_widget)
        splitter.setSizes([400, 800])
        
        calib_layout.addWidget(splitter)
        calib_widget.setLayout(calib_layout)
        self.tab_widget.addTab(calib_widget, "Calibración de Velocímetros")
    
    def convert_flow_to_m3_per_s(self, flow_value, unit_index):
        """Convierte el caudal a m³/s"""
        conversions = {
            0: flow_value / 3600,           # m³/h a m³/s
            1: flow_value / 3600000,        # L/h a m³/s
            2: flow_value / 60000,          # L/min a m³/s
            3: flow_value / 1000,           # L/s a m³/s
            4: flow_value,                  # m³/s
            5: flow_value * 0.00006309,     # GPM a m³/s
            6: flow_value * 0.00047194      # CFM a m³/s
        }
        return conversions.get(unit_index, 0)
    
    def calculate_velocity(self):
        """Calcula la velocidad del fluido en la tubería"""
        try:
            caudal_str = self.caudal_input.text().strip()
            diametro_str = self.diametro_input.text().strip()
            espesor_str = self.espesor_input.text().strip()
            
            if not caudal_str or not diametro_str or not espesor_str:
                QMessageBox.warning(self, "Error", "Por favor, complete todos los campos.")
                return
            
            caudal = float(caudal_str)
            diametro_exterior = float(diametro_str)
            espesor = float(espesor_str)
            
            if caudal <= 0 or diametro_exterior <= 0 or espesor < 0:
                QMessageBox.warning(self, "Error", "Valores inválidos.")
                return
            
            if espesor >= diametro_exterior / 2:
                QMessageBox.warning(self, "Error", "El espesor es demasiado grande.")
                return
            
            unit_index = self.caudal_units.currentIndex()
            caudal_m3_s = self.convert_flow_to_m3_per_s(caudal, unit_index)
            
            diametro_interior_mm = diametro_exterior - 2 * espesor
            diametro_interior_m = diametro_interior_mm / 1000
            area_m2 = math.pi * (diametro_interior_m / 2) ** 2
            velocidad = caudal_m3_s / area_m2
            
            unit_text = self.caudal_units.currentText().split('(')[1].split(')')[0]
            
            results = f"""
RESULTADOS DEL CÁLCULO:

Datos de entrada:
• Caudal: {caudal:,.2f} {unit_text}
• Diámetro exterior: {diametro_exterior:,.2f} mm
• Espesor de pared: {espesor:,.2f} mm

Cálculos intermedios:
• Diámetro interior: {diametro_interior_mm:,.2f} mm ({diametro_interior_m:.4f} m)
• Área de flujo: {area_m2:.6f} m²
• Caudal convertido: {caudal_m3_s:.6f} m³/s

VELOCIDAD RESULTANTE: {velocidad:.3f} m/s

Análisis: {self.analyze_velocity(velocidad)}
            """
            
            self.results_text.setText(results)
            
        except ValueError:
            QMessageBox.critical(self, "Error", "Valores numéricos inválidos.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")
    
    def analyze_velocity(self, velocity):
        """Analiza la velocidad"""
        if velocity < 0.5:
            return "Velocidad BAJA - Posible sedimentación"
        elif velocity <= 1.5:
            return "Velocidad ÓPTIMA para tuberías de agua"
        elif velocity <= 3.0:
            return "Velocidad ACEPTABLE - Monitorear erosión"
        elif velocity <= 5.0:
            return "Velocidad ALTA - Posible erosión y ruido"
        else:
            return "Velocidad MUY ALTA - REVISAR diseño"
    
    def add_calibration_point(self):
        """Agrega un punto de calibración"""
        try:
            # Validar campos
            diametro_str = self.calib_diametro.text().strip()
            espesor_str = self.calib_espesor.text().strip()
            caudal_str = self.calib_caudal.text().strip()
            velocidad_equipo_str = self.calib_velocidad_equipo.text().strip()
            
            if not all([diametro_str, espesor_str, caudal_str, velocidad_equipo_str]):
                QMessageBox.warning(self, "Error", "Complete todos los campos.")
                return
            
            # Convertir valores
            diametro_exterior = float(diametro_str)
            espesor = float(espesor_str)
            caudal = float(caudal_str)
            velocidad_equipo = float(velocidad_equipo_str)
            
            # Validaciones
            if diametro_exterior <= 0 or espesor < 0 or caudal <= 0:
                QMessageBox.warning(self, "Error", "Valores inválidos.")
                return
            
            if espesor >= diametro_exterior / 2:
                QMessageBox.warning(self, "Error", "Espesor demasiado grande.")
                return
            
            # Calcular velocidad patrón
            unit_index = self.calib_caudal_units.currentIndex()
            caudal_m3_s = self.convert_flow_to_m3_per_s(caudal, unit_index)
            
            diametro_interior_m = (diametro_exterior - 2 * espesor) / 1000
            area_m2 = math.pi * (diametro_interior_m / 2) ** 2
            velocidad_patron = caudal_m3_s / area_m2
            
            # Calcular error
            error = velocidad_equipo - velocidad_patron
            
            # Agregar punto
            punto = len(self.calibration_data) + 1
            self.calibration_data.append({
                'punto': punto,
                'velocidad_patron': velocidad_patron,
                'velocidad_equipo': velocidad_equipo,
                'error': error
            })
            
            # Actualizar tabla
            self.update_calibration_table()
            
            # Actualizar gráfico
            self.update_calibration_plot()
            
            # Limpiar campos de entrada
            self.calib_caudal.clear()
            self.calib_velocidad_equipo.clear()
            
            if len(self.calibration_data) >= 10:
                QMessageBox.information(self, "Calibración", 
                                      "Se han ingresado 10 puntos. Calibración completa.")
            
        except ValueError:
            QMessageBox.critical(self, "Error", "Valores numéricos inválidos.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")
    
    def update_calibration_table(self):
        """Actualiza la tabla de calibración"""
        self.calib_table.setRowCount(len(self.calibration_data))
        
        for i, data in enumerate(self.calibration_data):
            self.calib_table.setItem(i, 0, QTableWidgetItem(str(data['punto'])))
            self.calib_table.setItem(i, 1, QTableWidgetItem(f"{data['velocidad_patron']:.4f}"))
            self.calib_table.setItem(i, 2, QTableWidgetItem(f"{data['velocidad_equipo']:.4f}"))
            self.calib_table.setItem(i, 3, QTableWidgetItem(f"{data['error']:.4f}"))
    
    def update_calibration_plot(self):
        """Actualiza el gráfico de calibración"""
        if not self.calibration_data:
            self.plot_widget.clear_plot()
            return
        
        # Extraer datos
        velocity_patron = [d['velocidad_patron'] for d in self.calibration_data]
        errors = [d['error'] for d in self.calibration_data]
        
        # Calcular estadísticas
        statistics = {
            'mean_error': np.mean(errors),
            'std_error': np.std(errors, ddof=1) if len(errors) > 1 else 0,
            'max_error': max(errors),
            'min_error': min(errors)
        }
        
        # Actualizar gráfico
        self.plot_widget.update_plot(velocity_patron, errors, statistics)
        
        # Actualizar estadísticas en texto
        stats_text = f"""ESTADÍSTICAS DE CALIBRACIÓN:

Número de puntos: {len(self.calibration_data)}
Error promedio: {statistics['mean_error']:.4f} m/s
Desviación estándar: {statistics['std_error']:.4f} m/s
Error máximo: {statistics['max_error']:.4f} m/s
Error mínimo: {statistics['min_error']:.4f} m/s
Incertidumbre expandida (k=2): ±{2*statistics['std_error']:.4f} m/s

Rango de velocidades: {min(velocity_patron):.3f} - {max(velocity_patron):.3f} m/s
        """
        
        self.stats_text.setText(stats_text)
    
    def clear_calibration(self):
        """Limpia todos los datos de calibración"""
        reply = QMessageBox.question(self, 'Confirmar', 
                                   '¿Está seguro de limpiar todos los datos de calibración?',
                                   QMessageBox.Yes | QMessageBox.No, 
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.calibration_data.clear()
            self.calib_table.setRowCount(0)
            self.plot_widget.clear_plot()
            self.stats_text.clear()
    
    def export_results(self):
        """Exporta los resultados de calibración"""
        if not self.calibration_data:
            QMessageBox.warning(self, "Error", "No hay datos de calibración para exportar.")
            return
        
        try:
            # Crear reporte
            report = "REPORTE DE CALIBRACIÓN DE VELOCÍMETRO\n"
            report += "="*50 + "\n\n"
            
            # Configuración
            diametro = self.calib_diametro.text()
            espesor = self.calib_espesor.text()
            report += f"Configuración de tubería:\n"
            report += f"- Diámetro exterior: {diametro} mm\n"
            report += f"- Espesor de pared: {espesor} mm\n"
            report += f"- Diámetro interior: {float(diametro) - 2*float(espesor)} mm\n\n"
            
            # Datos
            report += "DATOS DE CALIBRACIÓN:\n"
            report += "-"*50 + "\n"
            report += f"{'Punto':<6} {'V.Patrón(m/s)':<12} {'V.Equipo(m/s)':<12} {'Error(m/s)':<10}\n"
            report += "-"*50 + "\n"
            
            for data in self.calibration_data:
                report += f"{data['punto']:<6} {data['velocidad_patron']:<12.4f} {data['velocidad_equipo']:<12.4f} {data['error']:<10.4f}\n"
            
            # Estadísticas
            errors = [d['error'] for d in self.calibration_data]
            mean_error = np.mean(errors)
            std_error = np.std(errors, ddof=1) if len(errors) > 1 else 0
            
            report += "\n" + "="*50 + "\n"
            report += "ESTADÍSTICAS:\n"
            report += f"- Error promedio: {mean_error:.4f} m/s\n"
            report += f"- Desviación estándar: {std_error:.4f} m/s\n"
            report += f"- Error máximo: {max(errors):.4f} m/s\n"
            report += f"- Error mínimo: {min(errors):.4f} m/s\n"
            report += f"- Incertidumbre expandida (k=2): ±{2*std_error:.4f} m/s\n"
            
            # Guardar archivo
            filename = f"calibracion_velocimetro_{len(self.calibration_data)}_puntos.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            
            QMessageBox.information(self, "Exportación", 
                                  f"Resultados exportados a: {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {str(e)}")
    
    def clear_fields(self):
        """Limpia todos los campos de la calculadora"""
        self.caudal_input.clear()
        self.diametro_input.clear()
        self.espesor_input.clear()
        self.results_text.clear()
        self.caudal_units.setCurrentIndex(0)

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Verificar dependencias
    try:
        import matplotlib
        matplotlib.use('Qt5Agg')
    except ImportError:
        QMessageBox.critical(None, "Error", 
                           "Matplotlib no está instalado.\n"
                           "Instale con: pip install matplotlib")
        sys.exit(1)
    
    calculator = PipeVelocityCalculator()
    calculator.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
