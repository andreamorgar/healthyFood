import pandas as pd
import json

# Cargar tabla
df = pd.read_csv("Colecciones_Auxiliares.FooDB_Solo_USDA_DTU_Corregida.csv")

# Crear un diccionario con el formato constituyente : (contenido-unidad)
def build_constituent_dict(sub_df):
    return dict(
        zip(
            sub_df['constituent'],
            sub_df['content'].astype(str) + ' ' + sub_df['unit']
        )
    )

# Agrupar y construir los diccionarios de constituyentes
constituents_df = df.groupby(['FooDB_ID', 'food_name']).apply(build_constituent_dict).reset_index(name='constituents')

# Obtener columnas adicionales (id y citation) - tomamos la primera aparición de cada grupo
extra_info = df.groupby(['FooDB_ID', 'food_name'])[['id', 'citation']].first().reset_index()

# Combinar ambas tablas por FooDB_ID y food_name
final_df = pd.merge(constituents_df, extra_info, on=['FooDB_ID', 'food_name'])
final_df.to_json("fooDB_Final.json", orient='records', indent=2)

with open("fooDB_Final.json", "r", encoding="utf-8") as f:
    data = json.load(f)  # lista de alimentos

# Convertir constituents a string JSON en cada objeto
for food in data:
    if "constituents" in food:
        food["constituents"] = json.dumps(food["constituents"], ensure_ascii=False)

# Guardar en nuevo archivo
with open("foods_flat.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
