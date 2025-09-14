from pymongo import MongoClient

# Requires the PyMongo package.
# https://api.mongodb.com/python/current

client = MongoClient('mongodb://localhost:27017/')
result = client['Envejecimiento_Saludable']['Envejecimiento_Saludable'].aggregate([
    {
        '$lookup': {
            'from': 'Food_Simplificada', 
            'localField': 'Food', 
            'foreignField': 'Name', 
            'as': 'Food_Info'
        }
    }, {
        '$unwind': {
            'path': '$Food_Info', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$addFields': {
            'FooDB_ID': '$Food_Info.FooDB_ID', 
            'group': '$Food_Info.group', 
            'subgroup': '$Food_Info.subgroup', 
            'group_id': '$Food_Info.group_id'
        }
    }, {
        '$project': {
            'Food_Info': 0
        }
    }
])