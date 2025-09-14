import pandas as pd

# Cargamos Tablas
df1 = pd.read_csv('FooDB.Nutrients.csv')   # Tabla de Nutrients o Compounds
df2 = pd.read_csv('Colecciones_Auxiliares.FooDB_Nutrientes_Corregidos.csv')  # Tabla FooDB_Solo_XXXXX
# Create a mapping from id to name
id_to_name = df1.set_index('id')['name']

# Replace orig_source_name in df2 by matching source_id
df2['orig_source_name'] = df2['orig_source_id'].map(id_to_name)# Save result if needed

df2.to_csv('filled_table.csv', index=False)
