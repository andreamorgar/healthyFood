from pymongo import MongoClient

# Requires the PyMongo package.
# https://api.mongodb.com/python/current

client = MongoClient('mongodb://localhost:27017/')
result = client['Colecciones_Auxiliares']['FooDB_Compuestos_Corregidos'].aggregate([
    {
        '$unionWith': {
            'coll': 'FooDB_Nutrientes_Corregidos'
        }
    }, {
        '$project': {
            'id': '$id', 
            'FooDB_ID': '$food_id', 
            'food_name': '$orig_food_common_name', 
            'constituent': '$orig_source_name', 
            'content': '$orig_content', 
            'constituent_unit': '$orig_unit', 
            'citation': '$citation'
        }
    }, {
        '$out': {
            'db': 'Colecciones_Auxiliares', 
            'coll': 'FooDB_Solo_USDA_DTU_Corregida'
        }
    }
])