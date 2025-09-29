import json
import math

#------ 1 CARGAR ARCHIVOS ------
with open("ES.json", "r", encoding="utf-8") as f:
    data = json.load(f)

#Si es un solo objeto, lo convertimos en lista
if isinstance(data, dict):
    data = [data]

#------ 2 CALCULAR RANGO DE DATOS ------
ranges = {}
for item in data:
    for key, value in item.items():
        if key == "Name":
            continue
        try:
            num_value = float(str(value).replace(",", "."))
        except ValueError:
            continue

        if key not in ranges:
            ranges[key] = {"min": num_value, "max": num_value}
        else:
            ranges[key]["min"] = min(ranges[key]["min"], num_value)
            ranges[key]["max"] = max(ranges[key]["max"], num_value)

#Guardamos los rangos en un archivo auxiliar
with open("ES_min_max.json", "w", encoding="utf-8") as f:
    json.dump(ranges, f, ensure_ascii=False, indent=2)
print(f"\nArchivo auxiliar guardado como ES_min_max.json")

#------ 3 OBTENEMOS EL VALOR DEL 1 AL 4 ------
def get_level(value, min_val, max_val):
    if max_val == min_val:
        return 0
    step = (max_val - min_val) / 5
    level = math.floor((value - min_val) / step)
    return min(max(level, 0), 4)

#------ 4 AÑADIMOS CAMPOS CON EL RANGO ------
for item in data:
    for key in list(item.keys()):
        if key == "Name":
            continue
        try:
            num_value = float(str(item[key]).replace(",", "."))
        except ValueError:
            continue

        if key in ranges:
            min_val = ranges[key]["min"]
            max_val = ranges[key]["max"]
            item[f"{key}_level"] = get_level(num_value, min_val, max_val)

#Guardamos el JSON resultado
with open("ES_Rango.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nArchivo final guardado como ES_Rango.json")
