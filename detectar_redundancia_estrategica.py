import pandas as pd
import networkx as nx
import sys
import itertools
from operator import itemgetter

RUTA_ARCHIVO_ARISTAS = "Aristas_Grafo_Dijkstra_Final.xlsx" # Nombre del archivo que contiene los datos del grafo
CANTIDAD_TOP_PARES = 10 # Cantidad de nodos maximos a evaluar
RUTA_ARCHIVO_SALIDA_EXCEL = "Top_Pares_Redundancia_Detallada.xlsx" # Nombre del archivo de salida

def formatear_camino_coordenadas(lista_coordenadas_camino):
    return " -> ".join([f"({coordenada[0]:.0f}, {coordenada[1]:.0f})" for coordenada in lista_coordenadas_camino]) # Formatear la arista entre nodos

def formatear_multiples_caminos(generador_caminos_independientes):
    lista_todos_los_caminos = list(generador_caminos_independientes) # Convertir los caminos en una lista
    
    if not lista_todos_los_caminos:
        return "No hay caminos independientes disponibles."

    lista_caminos_formateados = []
    for indice, camino in enumerate(lista_todos_los_caminos): # Iterando la lista de caminos
        lista_caminos_formateados.append(f"Camino {indice+1}: {formatear_camino_coordenadas(camino)}")
        
    return "\n".join(lista_caminos_formateados)

def detectar_pares_nodos_con_maxima_redundancia():
    try:
        dataframe_aristas_grafo = pd.read_excel(RUTA_ARCHIVO_ARISTAS)
    except Exception as error_carga:
        print(f"No se pudo cargar el archivo de aristas debido al siguiente error: {error_carga}.")
        return

    grafo_networkx_no_dirigido = nx.Graph() # Crear un grafo no dirigido

    for _, fila_arista in dataframe_aristas_grafo.iterrows():
        try:
            nodo_origen = (float(fila_arista["X_inicio"]), float(fila_arista["Y_inicio"]))
            nodo_destino = (float(fila_arista["X_fin"]), float(fila_arista["Y_fin"]))
            grafo_networkx_no_dirigido.add_edge(nodo_origen, nodo_destino) # Agregar la arista al grafo
        except ValueError:
            continue
            
    print(f"Se ha creado el grafo no dirigido con un total de {grafo_networkx_no_dirigido.number_of_nodes()} nodos.") # Crear el grafo no dirigido con todos los nodos

    lista_nodos_candidatos_mayor_grado = sorted(grafo_networkx_no_dirigido.degree, key=itemgetter(1), reverse=True)[:50] # Ordenar los nodos por grado
    lista_nodos_candidatos = [nodo for nodo, grado in lista_nodos_candidatos_mayor_grado] # Extraer los nodos candidatos
    
    lista_pares_nodos_a_analizar = list(itertools.combinations(lista_nodos_candidatos, 2)) # Generar todas las combinaciones de pares de nodos
    
    print(f"Se están analizando {len(lista_pares_nodos_a_analizar)} pares candidatos con mayor grado.")

    lista_resultados_conectividad = [] # List para almacenar los resultados de la conectividad
    
    for nodo_origen_par, nodo_destino_par in lista_pares_nodos_a_analizar:
        try:
            valor_conectividad_aristas = nx.edge_connectivity(grafo_networkx_no_dirigido, nodo_origen_par, nodo_destino_par) # Calcular la conectividad entre los nodos
            
            lista_resultados_conectividad.append({ # Agregar los resultados a la lista
                'Origen_Coord': formatear_camino_coordenadas([nodo_origen_par]),
                'Destino_Coord': formatear_camino_coordenadas([nodo_destino_par]),
                'Origen_FullCoord': nodo_origen_par, 
                'Destino_FullCoord': nodo_destino_par, 
                'Caminos_Disjuntos': valor_conectividad_aristas,
                'Camino_Detallado': None
            })
            
        except nx.NetworkXNoPath:
            lista_resultados_conectividad.append({
                'Origen_Coord': formatear_camino_coordenadas([nodo_origen_par]),
                'Destino_Coord': formatear_camino_coordenadas([nodo_destino_par]),
                'Origen_FullCoord': nodo_origen_par, 
                'Destino_FullCoord': nodo_destino_par, 
                'Caminos_Disjuntos': 0,
                'Camino_Detallado': 'No Conectado',
            })
        except Exception:
             pass 

    dataframe_resultados_conectividad = pd.DataFrame(lista_resultados_conectividad) # Convertir la lista en un dataframe
    dataframe_top_redundancia = dataframe_resultados_conectividad.sort_values(by='Caminos_Disjuntos', ascending=False).head(CANTIDAD_TOP_PARES).copy() # Ordenar los resultados por conectividad
    
    print(f"Se han identificado los 10 mejores pares y se están detallando los caminos independientes.")

    for indice_fila, fila_resultado in dataframe_top_redundancia.iterrows():
        nodo_origen_actual = fila_resultado['Origen_FullCoord']
        nodo_destino_actual = fila_resultado['Destino_FullCoord']
        valor_redundancia_actual = fila_resultado['Caminos_Disjuntos']

        if valor_redundancia_actual > 0:
            try:
                generador_caminos_independientes = nx.edge_disjoint_paths(grafo_networkx_no_dirigido, nodo_origen_actual, nodo_destino_actual)
                
                cadena_caminos_formateados = formatear_multiples_caminos(generador_caminos_independientes) # Formatear los caminos
                
                dataframe_top_redundancia.loc[indice_fila, 'Camino_Detallado'] = cadena_caminos_formateados # Agregar los caminos al dataframe
                
            except Exception as error_caminos:
                dataframe_top_redundancia.loc[indice_fila, 'Camino_Detallado'] = f"Error al obtener caminos: {error_caminos}"
        
    dataframe_top_redundancia['Nombre_Par'] = [f"PAR-{int(fila.Caminos_Disjuntos)}-{i+1}" 
                                         for i, fila in enumerate(dataframe_top_redundancia.itertuples())]
    
    lista_columnas_finales_exportar = ['Nombre_Par', 'Caminos_Disjuntos', 'Origen_Coord', 'Destino_Coord', 
                        'Camino_Detallado']

    dataframe_top_redundancia[lista_columnas_finales_exportar].to_excel(RUTA_ARCHIVO_SALIDA_EXCEL, index=False)
    
    print(f"El análisis se ha completado exitosamente para los {CANTIDAD_TOP_PARES} pares con mayor redundancia y el detalle de sus caminos.")
    print(f"El archivo '{RUTA_ARCHIVO_SALIDA_EXCEL}' ha sido generado correctamente.")
    print("La columna 'Camino_Detallado' contiene la lista de nodos para cada camino independiente.")
    print("A continuación se muestra una vista previa de los 10 mejores resultados.")
    print(dataframe_top_redundancia[['Nombre_Par', 'Caminos_Disjuntos', 'Origen_Coord', 'Destino_Coord']].to_markdown(index=False, numalign="left", stralign="left"))

if __name__ == "__main__":
    detectar_pares_nodos_con_maxima_redundancia()