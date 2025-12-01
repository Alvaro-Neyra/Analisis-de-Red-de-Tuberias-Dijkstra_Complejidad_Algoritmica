import pandas as pd
import random
import os
import numpy as np

def generar_aristas_para_algoritmo_dijkstra(ruta_archivo_vertices, ruta_salida_excel_aristas):
    try:
        dataframe_vertices_original = pd.read_excel(ruta_archivo_vertices, engine="openpyxl") 
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{ruta_archivo_vertices}'")
        return

    dataframe_vertices_procesado = dataframe_vertices_original[['OBJECTID', 'vertex_index', 'REALLENGTH', 'DIAMETER', 'X', 'Y']].copy() # Hacer un copia del archivo excel original pero con campos especificos
    dataframe_vertices_procesado = dataframe_vertices_procesado.drop_duplicates(subset=['OBJECTID', 'vertex_index'], keep='first') # Eliminar vertices duplicados
    dataframe_vertices_procesado = dataframe_vertices_procesado.sort_values(by=['OBJECTID', 'vertex_index']) # Ordenar los vertices de menor a mayor

    print(f"Registros cargados: {len(dataframe_vertices_procesado)}") 

    dataframe_extremos_tramos = dataframe_vertices_procesado.groupby('OBJECTID').agg(
        X_inicio=('X', 'first'),
        X_fin=('X', 'last'),
        Y_inicio=('Y', 'first'),
        Y_fin=('Y', 'last'),
        REALLENGTH=('REALLENGTH', 'first'),
        DIAMETER=('DIAMETER', 'first'),
    ).reset_index() # Agrupar los vertices por OBJECTID

    dataframe_extremos_tramos['PESO_FRICCION'] = np.where(
        dataframe_extremos_tramos['DIAMETER'] > 0,
        dataframe_extremos_tramos['REALLENGTH'] / dataframe_extremos_tramos['DIAMETER'],
        0
    ) # Calcular el peso de la fricción 

    lista_diccionarios_aristas = [] # Diccionario para representar el grafo

    for _, fila_tramo in dataframe_extremos_tramos.iterrows():
        peso_neto_calculado = fila_tramo['PESO_FRICCION'] # Extraemos el valor del peso de cada fila

        lista_diccionarios_aristas.append({
            'ID_TRAMO': fila_tramo['OBJECTID'],
            'X_inicio': fila_tramo['X_inicio'],
            'Y_inicio': fila_tramo['Y_inicio'],
            'X_fin': fila_tramo['X_fin'],
            'Y_fin': fila_tramo['Y_fin'],
            'PESO_FRICCION': fila_tramo['PESO_FRICCION'],
            'PESO_NETO': peso_neto_calculado,
            'DIRECCION': 'BIDIRECCIONAL'
        }) # Almacenamos cada fila en el diccionario ya con el peso calculado

    dataframe_final_aristas = pd.DataFrame(lista_diccionarios_aristas) # Convertimos el diccionario en un dataframe
    if os.path.exists(ruta_salida_excel_aristas):
        try:
            os.remove(ruta_salida_excel_aristas)
        except PermissionError:
            print(f"Error: No se puede sobrescribir '{ruta_salida_excel_aristas}'. Ciérrelo si está abierto.")
            return

    dataframe_final_aristas.to_excel(ruta_salida_excel_aristas, index=False) # Guardamos el dataframe en un archivo excel

    print("Archivo generado:", ruta_salida_excel_aristas)
    if not dataframe_final_aristas.empty:
        print("Peso mínimo generado:", dataframe_final_aristas['PESO_NETO'].min())
        print("Peso máximo generado:", dataframe_final_aristas['PESO_NETO'].max())
    else:
        print("Advertencia: No se generaron aristas.")

if __name__ == "__main__":
    generar_aristas_para_algoritmo_dijkstra(
        ruta_archivo_vertices='vertices_tuberia_primaria.xlsx',
        ruta_salida_excel_aristas='Aristas_Grafo_Dijkstra_Final.xlsx'
    )