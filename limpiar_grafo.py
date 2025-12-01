import pandas as pd

ruta_archivo_excel_aristas = "Aristas_Grafo_Dijkstra_Final.xlsx"

dataframe_original_aristas = pd.read_excel(ruta_archivo_excel_aristas)

dataframe_aristas_limpio = dataframe_original_aristas[
    ~((dataframe_original_aristas["X_inicio"] == dataframe_original_aristas["X_fin"]) & (dataframe_original_aristas["Y_inicio"] == dataframe_original_aristas["Y_fin"]))
].copy() # Eliminar las aristas que son iguales, para mejorar la eficiencia del algoritmo de dijkstra

dataframe_aristas_limpio.drop_duplicates(
    subset=["X_inicio", "Y_inicio", "X_fin", "Y_fin", "PESO_ARISTA"],
    inplace=True
) # Eliminar las aristas duplicadas

dataframe_aristas_limpio = dataframe_aristas_limpio[dataframe_aristas_limpio["PESO_ARISTA"] > 0] # Filtrar las aristas que no tienen peso negativo

dataframe_aristas_limpio.reset_index(drop=True, inplace=True) # Volver a ordenar los indices del dataframe

dataframe_aristas_limpio.to_excel(ruta_archivo_excel_aristas, index=False) # Guardar el dataframe limpio

print("Excel limpiado y reemplazado exitosamente.")
print("Registros antes:", len(dataframe_original_aristas))
print("Registros después:", len(dataframe_aristas_limpio))
