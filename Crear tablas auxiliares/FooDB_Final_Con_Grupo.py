from pymongo import MongoClient

# Requires the PyMongo package.
# https://api.mongodb.com/python/current

client = MongoClient('mongodb://localhost:27017/')
result = client['Colecciones_Finales']['FooDB_Alimento_Constituyentes'].aggregate([
    {
        '$lookup': {
            'from': 'Food_Simplificada', 
            'localField': 'FooDB_ID', 
            'foreignField': 'FooDB_ID', 
            'as': 'food_info'
        }
    }, {
        '$unwind': {
            'path': '$food_info', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$addFields': {
            'group': '$food_info.group', 
            'subgroup': '$food_info.subgroup', 
            'group_id': '$food_info.group_id'
        }
    }, {
        '$project': {
            'food_info': 0
        }
    }, {
        '$out': {
            'db': 'Colecciones_Finales', 
            'coll': 'FooDB_Alimento_Constituyentes'
        }
    }
])