from pymongo import MongoClient

# Requires the PyMongo package.
# https://api.mongodb.com/python/current

client = MongoClient('mongodb://localhost:27017/')
result = client['Colecciones_Auxiliares']['FooDB_Solo_USDA_DTU'].aggregate([
    {
        '$match': {
            'source_type': 'Compound'
        }
    }, {
        '$out': {
            'db': 'Colecciones_Auxiliares', 
            'coll': 'FooDB_Solo_Compuestos'
        }
    }
])