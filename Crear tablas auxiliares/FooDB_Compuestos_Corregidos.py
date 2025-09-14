from pymongo import MongoClient

# Requires the PyMongo package.
# https://api.mongodb.com/python/current

client = MongoClient('mongodb://localhost:27017/')
result = client['Colecciones_Auxiliares']['FooDB_Solo_Compuesto'].aggregate([
    {
        '$project': {
            'id': '$id', 
            'food_id': '$food_id', 
            'orig_food_common_name': '$orig_food_common_name', 
            'orig_source_name': '$orig_source_name', 
            'orig_content': '$orig_content', 
            'orig_unit': '$orig_unit', 
            'citation': '$citation'
        }
    }, {
        '$out': {
            'db': 'Colecciones_Auxiliares', 
            'coll': 'FooDB_Compuestos_Corregidos'
        }
    }
])