import sys
import math
import heapq
import re
import pandas as pd
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from typing import Dict, List, Tuple, Set, Optional

class ConfiguracionAplicacion: # Datos constantes de la configuracion de la aplicacion
    TITULO_APLICACION = "Análisis de Red de Tuberías - Dijkstra (No Dirigido)"
    RUTA_ARCHIVO_ARISTAS = "Aristas_Grafo_Dijkstra_Final.xlsx"
    RUTA_ARCHIVO_ESTRATEGICOS = "Top_Pares_Redundancia_Detallada.xlsx"
    
    RADIO_NODO_VISUALIZACION = 3.0
    COLOR_FONDO_GRAFO = QtGui.QColor("#1e1e1e")
    COLOR_ARISTA_NORMAL = QtGui.QColor("#555555")
    COLOR_ARISTA_SUBGRAFO = QtGui.QColor("#00aaff")
    COLOR_NODO_NORMAL = QtGui.QColor("#00aaff")
    COLOR_CAMINO_OPTIMO = QtGui.QColor("#ffd700")
    COLOR_NODO_ORIGEN = QtGui.QColor("#00ff00")
    COLOR_NODO_DESTINO = QtGui.QColor("#ff0000")

class CargadorGrafo: # Clase para cargar el grafo desde un archivo excel
    @staticmethod
    def cargar_grafo_desde_excel(ruta_archivo_excel):
        try:
            dataframe_excel = pd.read_excel(ruta_archivo_excel, engine="openpyxl") # Usando openpyxl para leer el archivo excel
        except FileNotFoundError:
            return {}

        diccionario_grafo = {} # Creamos un diccionario para almacenar los datos del grafo
        
        for _, fila_excel in dataframe_excel.iterrows():
            try:
                nodo_origen = (float(fila_excel["X_inicio"]), float(fila_excel["Y_inicio"]))
                nodo_destino = (float(fila_excel["X_fin"]), float(fila_excel["Y_fin"]))
                peso_arista = float(fila_excel["PESO_NETO"])
            except Exception:
                continue

            if nodo_origen not in diccionario_grafo: diccionario_grafo[nodo_origen] = []
            if nodo_destino not in diccionario_grafo: diccionario_grafo[nodo_destino] = []

            diccionario_grafo[nodo_origen].append((nodo_destino, peso_arista))
            diccionario_grafo[nodo_destino].append((nodo_origen, peso_arista))

        return diccionario_grafo

    @staticmethod
    def cargar_pares_estrategicos_desde_excel(ruta_archivo_excel): # Funcion para cargar los nodos que tienen mas redundancia
        try:
            dataframe_excel = pd.read_excel(ruta_archivo_excel, engine="openpyxl")
        except FileNotFoundError:
            return []

        lista_pares_estrategicos = []
        for _, fila_excel in dataframe_excel.iterrows():
            try:
                cadena_nodo_origen = str(fila_excel["Origen_Coord"]).replace('(', '').replace(')', '').split(',')
                coordenada_origen = (float(cadena_nodo_origen[0]), float(cadena_nodo_origen[1]))
                
                cadena_nodo_destino = str(fila_excel["Destino_Coord"]).replace('(', '').replace(')', '').split(',')
                coordenada_destino = (float(cadena_nodo_destino[0]), float(cadena_nodo_destino[1]))
                
                nombre_par_estrategico = str(fila_excel.get("ID_PAR", f"Par {_}"))
                
                cadena_caminos_detallados = str(fila_excel.get("Camino_Detallado", "")) # Obtenemos el camino detallado del par estrategico
                conjunto_nodos_subgrafo = set() # Conjunto para almacenar nodos
                conjunto_aristas_subgrafo = set() # Conjunto para almacenar aristas
                
                lista_lineas_caminos = cadena_caminos_detallados.split('\n')
                
                for linea_camino in lista_lineas_caminos:
                    if '->' in linea_camino:
                        lista_coordenadas_encontradas = re.findall(r"\((\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)\)", linea_camino) # Expresion regular que encuentra todas las coordenadas
                        
                        lista_nodos_camino_actual = []
                        for coordenada_x, coordenada_y in lista_coordenadas_encontradas: # Iteramos la lista de coordenadas
                            try:
                                nodo_actual = (float(coordenada_x), float(coordenada_y))
                                lista_nodos_camino_actual.append(nodo_actual)
                                conjunto_nodos_subgrafo.add(nodo_actual)
                            except ValueError:
                                pass
                        
                        for indice_nodo in range(len(lista_nodos_camino_actual) - 1):
                            nodo_u, nodo_v = lista_nodos_camino_actual[indice_nodo], lista_nodos_camino_actual[indice_nodo + 1]
                            arista_actual = (min(nodo_u, nodo_v), max(nodo_u, nodo_v))
                            conjunto_aristas_subgrafo.add(arista_actual) # Añadimos la arista al conjunto de aristas
                
                lista_pares_estrategicos.append((coordenada_origen, coordenada_destino, nombre_par_estrategico, conjunto_nodos_subgrafo, conjunto_aristas_subgrafo))
            except Exception:
                continue
        return lista_pares_estrategicos

class AnalizadorGrafo:
    @staticmethod
    def dijkstra(diccionario_grafo, nodo_inicio, nodo_fin): # Algoritmo de Dijkstra para encontrar el camino optimo
        diccionario_distancias = {nodo: math.inf for nodo in diccionario_grafo} # Iniciamos un diccionario de distancias con valor infinito
        diccionario_distancias[nodo_inicio] = 0
        diccionario_padres = {nodo: None for nodo in diccionario_grafo} # Iniciamos un diccionario de padres con valor None
        
        cola_prioridad = [(0, nodo_inicio)] # Iniciamos una cola de prioridad con el nodo inicio
        
        conjunto_visitados = set() # Iniciamos un conjunto de visitados

        while cola_prioridad:
            distancia_actual, nodo_actual = heapq.heappop(cola_prioridad)

            if distancia_actual > diccionario_distancias[nodo_actual]:
                continue
            
            if nodo_actual == nodo_fin:
                break

            conjunto_visitados.add(nodo_actual)
            if nodo_actual in diccionario_grafo:
                for nodo_vecino, peso_arista in diccionario_grafo[nodo_actual]:
                    if nodo_vecino in conjunto_visitados: continue
                    
                    nueva_distancia_calculada = distancia_actual + peso_arista
                    if nueva_distancia_calculada < diccionario_distancias[nodo_vecino]:
                        diccionario_distancias[nodo_vecino] = nueva_distancia_calculada
                        diccionario_padres[nodo_vecino] = nodo_actual
                        heapq.heappush(cola_prioridad, (nueva_distancia_calculada, nodo_vecino))

        lista_camino_optimo = []
        if diccionario_distancias[nodo_fin] != math.inf:
            nodo_rastreo = nodo_fin
            while nodo_rastreo is not None:
                lista_camino_optimo.append(nodo_rastreo)
                nodo_rastreo = diccionario_padres[nodo_rastreo]
            lista_camino_optimo.reverse()
        
        return diccionario_distancias[nodo_fin], lista_camino_optimo

class VisualizadorGrafo(QtWidgets.QWidget): # Clase para la visualización del grafo y la interacción con el usuario
    def __init__(self):
        super().__init__()
        self.datos_grafo_visualizar = {}
        self.conjunto_nodos_subgrafo = set()
        self.conjunto_aristas_subgrafo = set()
        self.lista_nodos_camino = []
        self.nodo_resaltar_origen = None
        self.nodo_resaltar_destino = None
        
        self.coordenada_minima_x = 0; self.coordenada_maxima_x = 100
        self.coordenada_minima_y = 0; self.coordenada_maxima_y = 100
        self.margen_visualizacion = 50
        self.factor_escala_zoom = 1.0
        self.traslacion_x = 0; self.traslacion_y = 0
        
        self.esta_arrastrando_vista = False
        self.ultima_posicion_raton = None
        self.usar_anti_alias = True
        
        self.setMouseTracking(True)

    def actualizar_datos_visualizacion(self, grafo, nodos_subgrafo=None, aristas_subgrafo=None, nodos_camino=None, origen=None, destino=None, forzar_centrado=False): # Método para actualizar los datos que se van a dibujar en el grafo
        self.datos_grafo_visualizar = grafo
        self.conjunto_nodos_subgrafo = nodos_subgrafo if nodos_subgrafo else set()
        self.conjunto_aristas_subgrafo = aristas_subgrafo if aristas_subgrafo else set()
        self.lista_nodos_camino = nodos_camino if nodos_camino else []
        self.nodo_resaltar_origen = origen
        self.nodo_resaltar_destino = destino
        
        if not self.datos_grafo_visualizar:
            self.update()
            return

        lista_coordenadas_x = [clave[0] for clave in self.datos_grafo_visualizar.keys()]
        lista_coordenadas_y = [clave[1] for clave in self.datos_grafo_visualizar.keys()]
        if lista_coordenadas_x and lista_coordenadas_y:
            self.coordenada_minima_x, self.coordenada_maxima_x = min(lista_coordenadas_x), max(lista_coordenadas_x)
            self.coordenada_minima_y, self.coordenada_maxima_y = min(lista_coordenadas_y), max(lista_coordenadas_y)
        
        if forzar_centrado:
            self.centrar_vista_grafo()
        
        self.update()

    def centrar_vista_grafo(self): # Método para centrar la vista del grafo en la pantalla
        ancho_mundo_real = self.coordenada_maxima_x - self.coordenada_minima_x
        alto_mundo_real = self.coordenada_maxima_y - self.coordenada_minima_y
        if ancho_mundo_real == 0: ancho_mundo_real = 1
        if alto_mundo_real == 0: alto_mundo_real = 1
        
        escala_x = (self.width() - 2 * self.margen_visualizacion) / ancho_mundo_real
        escala_y = (self.height() - 2 * self.margen_visualizacion) / alto_mundo_real
        self.factor_escala_zoom = min(escala_x, escala_y)
        
        centro_mundo_x = (self.coordenada_minima_x + self.coordenada_maxima_x) / 2
        centro_mundo_y = (self.coordenada_minima_y + self.coordenada_maxima_y) / 2
        
        centro_pantalla_x = self.width() / 2
        centro_pantalla_y = self.height() / 2
        
        self.traslacion_x = centro_pantalla_x - centro_mundo_x * self.factor_escala_zoom
        self.traslacion_y = centro_pantalla_y + centro_mundo_y * self.factor_escala_zoom

    def convertir_coordenadas_pantalla_a_mundo(self, coordenada_pantalla_x, coordenada_pantalla_y): # Convierte coordenadas de píxeles de la pantalla a coordenadas lógicas del grafo
        coordenada_mundo_x = (coordenada_pantalla_x - self.traslacion_x) / self.factor_escala_zoom
        coordenada_mundo_y = (coordenada_pantalla_y - self.traslacion_y) / -self.factor_escala_zoom
        return coordenada_mundo_x, coordenada_mundo_y

    def convertir_coordenadas_mundo_a_pantalla(self, coordenada_mundo_x, coordenada_mundo_y): # Convierte coordenadas lógicas del grafo a coordenadas de píxeles de la pantalla
        coordenada_pantalla_x = coordenada_mundo_x * self.factor_escala_zoom + self.traslacion_x
        coordenada_pantalla_y = self.traslacion_y - coordenada_mundo_y * self.factor_escala_zoom
        return coordenada_pantalla_x, coordenada_pantalla_y

    def mousePressEvent(self, evento_raton: QtGui.QMouseEvent) -> None:
        if evento_raton.button() == QtCore.Qt.MouseButton.LeftButton:
            self.esta_arrastrando_vista = True
            self.ultima_posicion_raton = evento_raton.position()
            self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(evento_raton)

    def mouseMoveEvent(self, evento_raton: QtGui.QMouseEvent) -> None: # Maneja el movimiento del ratón para desplazar (pan) la vista del grafo
        if self.esta_arrastrando_vista and self.ultima_posicion_raton is not None:
            posicion_actual = evento_raton.position()
            diferencia_x = posicion_actual.x() - self.ultima_posicion_raton.x()
            diferencia_y = posicion_actual.y() - self.ultima_posicion_raton.y()
            self.traslacion_x += diferencia_x; self.traslacion_y += diferencia_y
            self.ultima_posicion_raton = posicion_actual
            self.update()
        super().mouseMoveEvent(evento_raton)

    def mouseReleaseEvent(self, evento_raton: QtGui.QMouseEvent) -> None:
        if evento_raton.button() == QtCore.Qt.MouseButton.LeftButton and self.esta_arrastrando_vista:
            self.esta_arrastrando_vista = False
            self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(evento_raton)

    def wheelEvent(self, evento_rueda: QtGui.QWheelEvent) -> None: # Maneja el evento de la rueda del ratón para realizar zoom in/out
        delta_rueda = evento_rueda.angleDelta().y()
        if delta_rueda == 0:
            super().wheelEvent(evento_rueda); return
        factor_zoom = 1.001 ** delta_rueda
        nueva_escala_zoom = max(1e-6, min(self.factor_escala_zoom * factor_zoom, 1e6))
        posicion_pantalla_x, posicion_pantalla_y = evento_rueda.position().x(), evento_rueda.position().y()
        posicion_mundo_x, posicion_mundo_y = self.convertir_coordenadas_pantalla_a_mundo(posicion_pantalla_x, posicion_pantalla_y)
        self.factor_escala_zoom = nueva_escala_zoom
        self.traslacion_x = posicion_pantalla_x - posicion_mundo_x * self.factor_escala_zoom
        self.traslacion_y = posicion_pantalla_y + posicion_mundo_y * self.factor_escala_zoom
        self.update()
        super().wheelEvent(evento_rueda)

    def paintEvent(self, evento_pintura: QtGui.QPaintEvent) -> None: # Evento de pintura principal que dibuja todos los elementos del grafo
        pintor_qt = QtGui.QPainter(self)
        if self.usar_anti_alias: pintor_qt.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        pintor_qt.fillRect(self.rect(), ConfiguracionAplicacion.COLOR_FONDO_GRAFO)

        self.dibujar_todas_las_aristas(pintor_qt)
        self.dibujar_todos_los_nodos(pintor_qt)
        self.dibujar_subgrafo_seleccionado(pintor_qt)
        self.dibujar_pesos_aristas_subgrafo(pintor_qt)
        self.dibujar_camino_optimo_encontrado(pintor_qt)
        self.dibujar_nodos_origen_destino_resaltados(pintor_qt)

    def dibujar_todas_las_aristas(self, pintor_qt: QtGui.QPainter):
        pluma_arista = QtGui.QPen(ConfiguracionAplicacion.COLOR_ARISTA_NORMAL)
        pluma_arista.setWidthF(max(0.5, 1.0 * (1.0 if self.factor_escala_zoom >= 1.0 else self.factor_escala_zoom)))
        pintor_qt.setPen(pluma_arista)
        
        for nodo_u in self.datos_grafo_visualizar:
            pantalla_x1, pantalla_y1 = self.convertir_coordenadas_mundo_a_pantalla(nodo_u[0], nodo_u[1])
            for nodo_v, _ in self.datos_grafo_visualizar[nodo_u]:
                if nodo_u < nodo_v:
                    pantalla_x2, pantalla_y2 = self.convertir_coordenadas_mundo_a_pantalla(nodo_v[0], nodo_v[1])
                    pintor_qt.drawLine(QtCore.QPointF(pantalla_x1, pantalla_y1), QtCore.QPointF(pantalla_x2, pantalla_y2))

    def dibujar_todos_los_nodos(self, pintor_qt: QtGui.QPainter):
        pincel_nodo = QtGui.QBrush(ConfiguracionAplicacion.COLOR_NODO_NORMAL.lighter(180))
        pintor_qt.setBrush(pincel_nodo)
        pluma_nodo = QtGui.QPen(ConfiguracionAplicacion.COLOR_NODO_NORMAL.lighter(150))
        pluma_nodo.setWidthF(0.5)
        pintor_qt.setPen(pluma_nodo)
        for (coordenada_x, coordenada_y) in self.datos_grafo_visualizar.keys():
            pantalla_x, pantalla_y = self.convertir_coordenadas_mundo_a_pantalla(coordenada_x, coordenada_y)
            radio_nodo = max(1.0, ConfiguracionAplicacion.RADIO_NODO_VISUALIZACION * (1.0 if self.factor_escala_zoom >= 1.0 else self.factor_escala_zoom))
            pintor_qt.drawEllipse(QtCore.QPointF(pantalla_x, pantalla_y), radio_nodo, radio_nodo)

    def dibujar_subgrafo_seleccionado(self, pintor_qt: QtGui.QPainter):
        if not self.conjunto_nodos_subgrafo: return
        pluma_subarista = QtGui.QPen(ConfiguracionAplicacion.COLOR_ARISTA_SUBGRAFO)
        pluma_subarista.setWidthF(max(1.0, 2.0 * (1.0 if self.factor_escala_zoom >= 1.0 else self.factor_escala_zoom)))
        pintor_qt.setPen(pluma_subarista)
        
        pluma_subarista.setWidthF(max(1.0, 2.0 * (1.0 if self.factor_escala_zoom >= 1.0 else self.factor_escala_zoom)))
        pintor_qt.setPen(pluma_subarista)
        
        for arista_subgrafo in self.conjunto_aristas_subgrafo:
            nodo_u, nodo_v = arista_subgrafo
            pantalla_x1, pantalla_y1 = self.convertir_coordenadas_mundo_a_pantalla(nodo_u[0], nodo_u[1])
            pantalla_x2, pantalla_y2 = self.convertir_coordenadas_mundo_a_pantalla(nodo_v[0], nodo_v[1])
            pintor_qt.drawLine(QtCore.QPointF(pantalla_x1, pantalla_y1), QtCore.QPointF(pantalla_x2, pantalla_y2))

        pintor_qt.setBrush(QtGui.QBrush(ConfiguracionAplicacion.COLOR_NODO_NORMAL))
        pluma_subnodo = QtGui.QPen(ConfiguracionAplicacion.COLOR_ARISTA_SUBGRAFO.darker(150))
        pluma_subnodo.setWidthF(1.0)
        pintor_qt.setPen(pluma_subnodo)
        for (coordenada_x, coordenada_y) in self.conjunto_nodos_subgrafo:
            pantalla_x, pantalla_y = self.convertir_coordenadas_mundo_a_pantalla(coordenada_x, coordenada_y)
            radio_nodo = max(1.5, ConfiguracionAplicacion.RADIO_NODO_VISUALIZACION * (1.5 if self.factor_escala_zoom >= 1.0 else self.factor_escala_zoom))
            pintor_qt.drawEllipse(QtCore.QPointF(pantalla_x, pantalla_y), radio_nodo, radio_nodo)

    def dibujar_pesos_aristas_subgrafo(self, pintor_qt: QtGui.QPainter):
        if not self.conjunto_aristas_subgrafo: return
        
        pintor_qt.setFont(QtGui.QFont("Arial", 8, QtGui.QFont.Weight.Bold))
        
        for arista_subgrafo in self.conjunto_aristas_subgrafo:
            nodo_u, nodo_v = arista_subgrafo
            
            if nodo_u not in self.datos_grafo_visualizar: continue
            peso_arista = None
            for vecino, peso in self.datos_grafo_visualizar[nodo_u]:
                if vecino == nodo_v:
                    peso_arista = peso
                    break
            
            if peso_arista is None: continue
            
            pantalla_x1, pantalla_y1 = self.convertir_coordenadas_mundo_a_pantalla(nodo_u[0], nodo_u[1])
            pantalla_x2, pantalla_y2 = self.convertir_coordenadas_mundo_a_pantalla(nodo_v[0], nodo_v[1])
            
            punto_medio_x = (pantalla_x1 + pantalla_x2) / 2
            punto_medio_y = (pantalla_y1 + pantalla_y2) / 2
            
            rectangulo_texto = QtCore.QRectF(punto_medio_x - 30, punto_medio_y - 10, 60, 20)
            pintor_qt.fillRect(rectangulo_texto, QtGui.QColor(30, 30, 45, 200))
            pintor_qt.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))
            pintor_qt.drawText(rectangulo_texto, QtCore.Qt.AlignmentFlag.AlignCenter, f"{peso_arista:.4g}")

    def dibujar_camino_optimo_encontrado(self, pintor_qt: QtGui.QPainter):
        if not (self.lista_nodos_camino and len(self.lista_nodos_camino) >= 2): return
        pluma_camino = QtGui.QPen(ConfiguracionAplicacion.COLOR_CAMINO_OPTIMO)
        pluma_camino.setWidthF(max(0.5, 1.0 * (1.0 if self.factor_escala_zoom >= 1.0 else self.factor_escala_zoom)))
        pintor_qt.setPen(pluma_camino)
        for indice_nodo in range(len(self.lista_nodos_camino) - 1):
            nodo_a = self.lista_nodos_camino[indice_nodo]; nodo_b = self.lista_nodos_camino[indice_nodo + 1]
            pantalla_x1, pantalla_y1 = self.convertir_coordenadas_mundo_a_pantalla(nodo_a[0], nodo_a[1]); pantalla_x2, pantalla_y2 = self.convertir_coordenadas_mundo_a_pantalla(nodo_b[0], nodo_b[1])
            pintor_qt.drawLine(QtCore.QPointF(pantalla_x1, pantalla_y1), QtCore.QPointF(pantalla_x2, pantalla_y2))

        pintor_qt.setBrush(QtGui.QBrush(ConfiguracionAplicacion.COLOR_CAMINO_OPTIMO.lighter(150)))
        pintor_qt.setPen(QtGui.QPen(ConfiguracionAplicacion.COLOR_CAMINO_OPTIMO.darker(150)))
        for nodo_camino in self.lista_nodos_camino:
            pantalla_x, pantalla_y = self.convertir_coordenadas_mundo_a_pantalla(*nodo_camino)
            radio_nodo = max(1.0, ConfiguracionAplicacion.RADIO_NODO_VISUALIZACION * (1.0 if self.factor_escala_zoom >= 1.0 else self.factor_escala_zoom))
            pintor_qt.drawEllipse(QtCore.QPointF(pantalla_x, pantalla_y), radio_nodo, radio_nodo)

    def dibujar_nodos_origen_destino_resaltados(self, pintor_qt: QtGui.QPainter):
        radio_nodo = max(1.0, ConfiguracionAplicacion.RADIO_NODO_VISUALIZACION * (1.0 if self.factor_escala_zoom >= 1.0 else self.factor_escala_zoom))
        
        if self.nodo_resaltar_origen:
            pantalla_x, pantalla_y = self.convertir_coordenadas_mundo_a_pantalla(*self.nodo_resaltar_origen)
            pintor_qt.setBrush(QtGui.QBrush(ConfiguracionAplicacion.COLOR_NODO_ORIGEN))
            pintor_qt.setPen(QtGui.QPen(ConfiguracionAplicacion.COLOR_NODO_ORIGEN.darker(150), 1))
            pintor_qt.drawEllipse(QtCore.QPointF(pantalla_x, pantalla_y), radio_nodo, radio_nodo)
            pintor_qt.drawText(QtCore.QRectF(pantalla_x - 20, pantalla_y - 20, 40, 20), QtCore.Qt.AlignmentFlag.AlignCenter, "INICIO")
            
        if self.nodo_resaltar_destino:
            pantalla_x, pantalla_y = self.convertir_coordenadas_mundo_a_pantalla(*self.nodo_resaltar_destino)
            pintor_qt.setBrush(QtGui.QBrush(ConfiguracionAplicacion.COLOR_NODO_DESTINO))
            pintor_qt.setPen(QtGui.QPen(ConfiguracionAplicacion.COLOR_NODO_DESTINO.darker(150), 1))
            pintor_qt.drawEllipse(QtCore.QPointF(pantalla_x, pantalla_y), radio_nodo, radio_nodo)
            pintor_qt.drawText(QtCore.QRectF(pantalla_x - 20, pantalla_y + 10, 40, 20), QtCore.Qt.AlignmentFlag.AlignCenter, "FIN")


class VentanaPrincipal(QtWidgets.QMainWindow): # Clase principal de la aplicación que gestiona la interfaz y la lógica
    def __init__(self):
        super().__init__()
        self.setWindowTitle(ConfiguracionAplicacion.TITULO_APLICACION)
        self.resize(1200, 800)

        app_icon = QIcon()
        app_icon.addFile("icono.png", QSize(64, 64))
        self.setWindowIcon(app_icon)

        self.diccionario_grafo_completo: Dict[Tuple[float, float], List[Tuple[Tuple[float, float], float]]] = {}
        self.lista_datos_pares_estrategicos: List[Tuple[Tuple[float, float], Tuple[float, float], str, Set[Tuple[float, float]], Set[Tuple[Tuple[float, float], Tuple[float, float]]]]] = []
        self.nodo_origen_actual: Optional[Tuple[float, float]] = None
        self.nodo_destino_actual: Optional[Tuple[float, float]] = None
        self.costo_minimo_calculado: Optional[float] = None
        self.lista_camino_encontrado: List[Tuple[float, float]] = []
        self.conjunto_nodos_subgrafo_activo: Set[Tuple[float, float]] = set()
        self.conjunto_aristas_subgrafo_activo: Set[Tuple[Tuple[float, float], Tuple[float, float]]] = set()

        self.inicializar_interfaz_usuario()
        self.cargar_datos_iniciales_y_grafo()

    def inicializar_interfaz_usuario(self): # Inicializa y configura los elementos de la interfaz de usuario
        widget_central = QtWidgets.QWidget()
        self.setCentralWidget(widget_central)
        diseno_principal = QtWidgets.QHBoxLayout(widget_central)

        self.widget_visualizador_grafo = VisualizadorGrafo()

        panel_control = QtWidgets.QWidget()
        diseno_control = QtWidgets.QVBoxLayout(panel_control)
        diseno_control.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        etiqueta_titulo = QtWidgets.QLabel(f"<h2>{ConfiguracionAplicacion.TITULO_APLICACION}</h2>")
        etiqueta_titulo.setTextFormat(QtCore.Qt.TextFormat.RichText)
        diseno_control.addWidget(etiqueta_titulo)

        self.combobox_seleccion_par_estrategico = QtWidgets.QComboBox()
        self.combobox_seleccion_par_estrategico.addItem("Seleccionar Par Estratégico (Origen → Destino)")
        self.combobox_seleccion_par_estrategico.currentIndexChanged.connect(self.actualizar_seleccion_par_estrategico)
        diseno_control.addWidget(QtWidgets.QLabel("Par de Nodos Estratégicos:"))
        diseno_control.addWidget(self.combobox_seleccion_par_estrategico)

        fila_botones = QtWidgets.QHBoxLayout()
        self.boton_calcular_camino = QtWidgets.QPushButton("Calcular Camino Óptimo")
        self.boton_calcular_camino.clicked.connect(self.calcular_camino_optimo_entre_nodos)
        self.boton_calcular_camino.setEnabled(False)
        fila_botones.addWidget(self.boton_calcular_camino)

        self.boton_resetear_seleccion = QtWidgets.QPushButton("Resetear")
        self.boton_resetear_seleccion.clicked.connect(self.resetear_seleccion_actual)
        fila_botones.addWidget(self.boton_resetear_seleccion)
        diseno_control.addLayout(fila_botones)

        diseno_control.addWidget(QtWidgets.QLabel("Resultado del Análisis:"))
        self.navegador_resultados_analisis = QtWidgets.QTextBrowser()
        self.navegador_resultados_analisis.setOpenExternalLinks(True)
        self.navegador_resultados_analisis.setMinimumHeight(140)
        self.navegador_resultados_analisis.setStyleSheet("border-radius:6px; padding:8px;")
        diseno_control.addWidget(self.navegador_resultados_analisis)

        widget_leyenda = QtWidgets.QWidget()
        diseno_leyenda = QtWidgets.QHBoxLayout(widget_leyenda)
        diseno_leyenda.setContentsMargins(0,0,0,0)
        diseno_leyenda.addWidget(self.crear_widget_chip_leyenda("Origen", ConfiguracionAplicacion.COLOR_NODO_ORIGEN))
        diseno_leyenda.addWidget(self.crear_widget_chip_leyenda("Destino", ConfiguracionAplicacion.COLOR_NODO_DESTINO))
        diseno_leyenda.addWidget(self.crear_widget_chip_leyenda("Redundancia", ConfiguracionAplicacion.COLOR_ARISTA_SUBGRAFO))
        diseno_leyenda.addWidget(self.crear_widget_chip_leyenda("Camino óptimo", ConfiguracionAplicacion.COLOR_CAMINO_OPTIMO))
        diseno_control.addWidget(widget_leyenda)

        diseno_control.addStretch()

        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2f; }
            QWidget { color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
            QLabel { color: #e0e0e0; }
            
            QComboBox {
                background-color: #2d2d44;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 6px;
                min-width: 200px;
            }
            QComboBox::drop-down { border: 0px; }
            QComboBox QAbstractItemView {
                background-color: #2d2d44;
                color: #ffffff;
                selection-background-color: #00d4ff;
                selection-color: #000000;
            }

            QPushButton {
                background-color: #00d4ff;
                color: #1e1e2f;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #33e0ff; }
            QPushButton:pressed { background-color: #00aacc; }
            QPushButton:disabled { background-color: #444; color: #888; }

            QTextBrowser {
                background-color: #2d2d44;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 6px;
            }
        """)

        diseno_principal.addWidget(self.widget_visualizador_grafo, 4)
        diseno_principal.addWidget(panel_control, 1)
        self.barra_estado = self.statusBar()

    def crear_widget_chip_leyenda(self, texto_etiqueta: str, color_chip: QtGui.QColor) -> QtWidgets.QWidget:
        widget_chip = QtWidgets.QWidget()
        diseno_chip = QtWidgets.QHBoxLayout(widget_chip)
        diseno_chip.setContentsMargins(0, 0, 0, 0)
        diseno_chip.setSpacing(5)
        
        etiqueta_color = QtWidgets.QLabel()
        mapa_pixeles = QtGui.QPixmap(12, 12)
        mapa_pixeles.fill(color_chip)
        etiqueta_color.setPixmap(mapa_pixeles)
        etiqueta_color.setFixedSize(12, 12)
        
        etiqueta_texto = QtWidgets.QLabel(texto_etiqueta)
        etiqueta_texto.setStyleSheet("color: black; font-weight: bold; background: transparent; border-color: transparent;")
        
        diseno_chip.addWidget(etiqueta_color)
        diseno_chip.addWidget(etiqueta_texto)
        
        widget_chip.setStyleSheet("background: rgba(45, 45, 68, 200); border-radius: 6px; padding: 4px; border: 1px solid #444; border-color: transparent;")
        return widget_chip

    def cargar_datos_iniciales_y_grafo(self): # Carga los datos del grafo y los pares estratégicos al inicio
        self.diccionario_grafo_completo = CargadorGrafo.cargar_grafo_desde_excel(ConfiguracionAplicacion.RUTA_ARCHIVO_ARISTAS)
        self.lista_datos_pares_estrategicos = CargadorGrafo.cargar_pares_estrategicos_desde_excel(ConfiguracionAplicacion.RUTA_ARCHIVO_ESTRATEGICOS)

        if not self.diccionario_grafo_completo:
            self.barra_estado.showMessage("Error: No se pudo cargar el grafo completo.")
            return

        self.combobox_seleccion_par_estrategico.blockSignals(True)
        for indice_par, (nodo_origen, nodo_destino, nombre_par, _, _) in enumerate(self.lista_datos_pares_estrategicos):
            cadena_origen = f"({nodo_origen[0]:.0f}, {nodo_origen[1]:.0f})"
            cadena_destino = f"({nodo_destino[0]:.0f}, {nodo_destino[1]:.0f})"
            nombre_limpio_par = nombre_par.split("(Redundancia:")[0].strip()
            self.combobox_seleccion_par_estrategico.addItem(f"{nombre_limpio_par}: {cadena_origen} → {cadena_destino}", userData=indice_par)
        self.combobox_seleccion_par_estrategico.blockSignals(False)

        self.widget_visualizador_grafo.actualizar_datos_visualizacion(self.diccionario_grafo_completo, nodos_subgrafo=set(), forzar_centrado=True)
        self.actualizar_estado_interfaz_usuario()
        self.barra_estado.showMessage(f"Grafo cargado. Nodos base: {len(self.diccionario_grafo_completo)}. Pares: {len(self.lista_datos_pares_estrategicos)}")

    def actualizar_seleccion_par_estrategico(self): # Actualiza la vista cuando el usuario selecciona un par estratégico diferente
        indice_seleccionado = self.combobox_seleccion_par_estrategico.currentData()
        if isinstance(indice_seleccionado, int) and 0 <= indice_seleccionado < len(self.lista_datos_pares_estrategicos):
            datos_par = self.lista_datos_pares_estrategicos[indice_seleccionado]
            self.nodo_origen_actual, self.nodo_destino_actual, _, self.conjunto_nodos_subgrafo_activo, self.conjunto_aristas_subgrafo_activo = datos_par
            self.navegador_resultados_analisis.setHtml("")
        else:
            self.nodo_origen_actual, self.nodo_destino_actual = None, None
            self.conjunto_nodos_subgrafo_activo = set()
            self.conjunto_aristas_subgrafo_activo = set()
            self.navegador_resultados_analisis.setHtml("<i>Seleccione un par estratégico para habilitar el cálculo.</i>")

        self.lista_camino_encontrado = []
        self.actualizar_estado_interfaz_usuario()

    def actualizar_estado_interfaz_usuario(self):
        es_seleccion_valida = self.nodo_origen_actual is not None and self.nodo_destino_actual is not None
        self.boton_calcular_camino.setEnabled(es_seleccion_valida)

        nodos_para_subgrafo = self.conjunto_nodos_subgrafo_activo
        self.widget_visualizador_grafo.actualizar_datos_visualizacion(
            self.diccionario_grafo_completo,
            nodos_subgrafo=nodos_para_subgrafo,
            aristas_subgrafo=self.conjunto_aristas_subgrafo_activo,
            nodos_camino=self.lista_camino_encontrado,
            origen=self.nodo_origen_actual,
            destino=self.nodo_destino_actual,
            forzar_centrado=False
        )

        if es_seleccion_valida and not self.lista_camino_encontrado:
            texto_estado = f"<b>Listo para calcular ruta óptima</b><br>{self.combobox_seleccion_par_estrategico.currentText()}<br><small>Pulse 'Calcular Camino Óptimo'.</small>"
            self.navegador_resultados_analisis.setHtml(texto_estado)
        elif not es_seleccion_valida and not self.lista_camino_encontrado:
            self.navegador_resultados_analisis.setHtml("<i>Esperando selección de un Par Estratégico (Origen → Destino).</i>")

    def resetear_seleccion_actual(self):
        self.nodo_origen_actual = None
        self.nodo_destino_actual = None
        self.lista_camino_encontrado = []
        self.costo_minimo_calculado = None
        self.conjunto_nodos_subgrafo_activo = set()
        self.conjunto_aristas_subgrafo_activo = set()
        self.combobox_seleccion_par_estrategico.setCurrentIndex(0)
        self.actualizar_estado_interfaz_usuario()
        self.barra_estado.showMessage("Selección reseteada.")

    def mostrar_alerta_mensaje_html(self, titulo_ventana: str, mensaje_html: str, nivel_alerta: str = 'info'):
        cuadro_mensaje = QtWidgets.QMessageBox(self)
        cuadro_mensaje.setWindowTitle(titulo_ventana)
        cuadro_mensaje.setTextFormat(QtCore.Qt.TextFormat.RichText)
        if nivel_alerta == 'warning':
            cuadro_mensaje.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        elif nivel_alerta == 'critical':
            cuadro_mensaje.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        else:
            cuadro_mensaje.setIcon(QtWidgets.QMessageBox.Icon.Information)
        cuadro_mensaje.setText(mensaje_html)
        cuadro_mensaje.exec()

    def calcular_camino_optimo_entre_nodos(self): # Ejecuta el algoritmo de Dijkstra para encontrar el camino más corto
        nodo_origen = self.nodo_origen_actual
        nodo_destino = self.nodo_destino_actual
        if not (nodo_origen and nodo_destino): return

        try:
            distancia_total_calculada, camino_calculado = AnalizadorGrafo.dijkstra(self.diccionario_grafo_completo, nodo_origen, nodo_destino)
        except Exception as error_dijkstra:
            self.mostrar_alerta_mensaje_html("Error Crítico de Cálculo", f"<b>Error en Dijkstra:</b> {error_dijkstra}", nivel_alerta='critical')
            return

        if not camino_calculado or distancia_total_calculada == math.inf:
            mensaje_resultado = (
                f"<div style='padding:10px; border:1px solid #ff4444; border-radius:6px; background: rgba(255,0,0,0.1);'>"
                f"<h3 style='margin:0; color:#ff4444;'>❌ Camino No Encontrado</h3>"
                f"<p><b>Motivo:</b> El nodo destino es inalcanzable desde el origen (Grafo desconectado).</p>"
                f"</div>"
            )
            self.lista_camino_encontrado = []
            self.navegador_resultados_analisis.setHtml(mensaje_resultado)
        else:
            self.costo_minimo_calculado = distancia_total_calculada
            self.lista_camino_encontrado = camino_calculado
            mensaje_resultado = (
                f"<div style='padding: 12px; border-radius:8px; background:transparent;'>"
                f"<h3 style='margin:0;'>✅ Camino Óptimo Encontrado</h3>"
                f"<div style='font-size:22px; color:{ConfiguracionAplicacion.COLOR_CAMINO_OPTIMO.name()};'><b>{distancia_total_calculada:.4f}</b></div>"
                f"<p><b>Pasos:</b> {len(camino_calculado) - 1} tramos</p>"
                f"</div>"
            )
            self.navegador_resultados_analisis.setHtml(mensaje_resultado)

        self.actualizar_estado_interfaz_usuario()
        self.barra_estado.showMessage(f"Cálculo completado. Costo: {distancia_total_calculada:.4f}")

class VentanaCarga(QtWidgets.QWidget): # Ventana de carga inicial para mostrar el progreso de inicio de la aplicación
    def __init__(self):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(600, 350)
        self.setWindowTitle("Carga de datos")
        app_icon = QIcon()
        app_icon.addFile("icono.png", QSize(64, 64))
        self.setWindowIcon(app_icon)
        
        self.setStyleSheet("""
            QWidget#CentralWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e1e2f, stop:1 #2d2d44);
                border-radius: 20px;
                border: 1px solid #444;
            }
            QLabel { color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
            QProgressBar {
                background-color: #333;
                border-radius: 5px;
                height: 8px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #00d4ff;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #00d4ff;
                color: #1e1e2f;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #33e0ff;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)

        self.widget_central = QtWidgets.QWidget(self)
        self.widget_central.setObjectName("CentralWidget")
        self.widget_central.setGeometry(0, 0, 600, 350)
        
        diseno_vertical = QtWidgets.QVBoxLayout(self.widget_central)
        diseno_vertical.setContentsMargins(40, 40, 40, 40)
        diseno_vertical.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        etiqueta_titulo = QtWidgets.QLabel(ConfiguracionAplicacion.TITULO_APLICACION)
        etiqueta_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        etiqueta_titulo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        etiqueta_titulo.setWordWrap(True)
        diseno_vertical.addWidget(etiqueta_titulo)
        
        diseno_vertical.addSpacing(30)

        self.barra_progreso = QtWidgets.QProgressBar()
        self.barra_progreso.setMaximum(100)
        self.barra_progreso.setValue(0)
        self.barra_progreso.setTextVisible(False)
        diseno_vertical.addWidget(self.barra_progreso)
        
        diseno_vertical.addSpacing(15)

        self.etiqueta_estado = QtWidgets.QLabel("Iniciando componentes...")
        self.etiqueta_estado.setStyleSheet("font-size: 14px; color: #aaaaaa;")
        self.etiqueta_estado.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        diseno_vertical.addWidget(self.etiqueta_estado)

        diseno_vertical.addSpacing(30)

        self.boton_iniciar = QtWidgets.QPushButton("INICIAR SISTEMA")
        self.boton_iniciar.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.boton_iniciar.setEnabled(False)
        self.boton_iniciar.clicked.connect(self.iniciar_aplicacion_principal)
        diseno_vertical.addWidget(self.boton_iniciar)

        self.valor_progreso_actual = 0
        self.temporizador = QtCore.QTimer()
        self.temporizador.timeout.connect(self.actualizar_progreso_carga)
        self.temporizador.start(20)

        self.ventana_principal = None

    def actualizar_progreso_carga(self): # Actualiza la barra de progreso y el estado de carga
        self.valor_progreso_actual += 1
        if self.valor_progreso_actual > 100: self.valor_progreso_actual = 100
        self.barra_progreso.setValue(self.valor_progreso_actual)

        if self.valor_progreso_actual >= 100:
            self.temporizador.stop()
            self.etiqueta_estado.setText("Carga completa. ¡Listo!")
            self.boton_iniciar.setEnabled(True)
        elif self.valor_progreso_actual > 60:
            self.etiqueta_estado.setText("Inicializando algoritmos y estructuras...")
        elif self.valor_progreso_actual > 20:
            self.etiqueta_estado.setText("Cargando datos del grafo...")

    def iniciar_aplicacion_principal(self): # Cierra la ventana de carga e inicia la ventana principal de la aplicación
        self.ventana_principal = VentanaPrincipal()
        self.ventana_principal.show()
        self.close()

def main():
    aplicacion = QtWidgets.QApplication(sys.argv)
    ventana_inicio = VentanaCarga()
    ventana_inicio.show()
    sys.exit(aplicacion.exec())


if __name__ == "__main__":
    main()
