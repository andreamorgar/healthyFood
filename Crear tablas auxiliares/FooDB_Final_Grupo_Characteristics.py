from pymongo import MongoClient

# Requires the PyMongo package.
# https://api.mongodb.com/python/current

client = MongoClient('mongodb://localhost:27017/')
result = client['Colecciones_Finales']['FooDB_Alimento_Constituyentes'].aggregate([
    {
        '$addFields': {
            'name_parts': {
                '$split': [
                    '$food_name', ','
                ]
            }
        }
    }, {
        '$addFields': {
            'food_name': {
                '$arrayElemAt': [
                    '$name_parts', 0
                ]
            }, 
            'characteristics': {
                '$cond': {
                    'if': {
                        '$gt': [
                            {
                                '$size': '$name_parts'
                            }, 1
                        ]
                    }, 
                    'then': {
                        '$trim': {
                            'input': {
                                '$reduce': {
                                    'input': {
                                        '$slice': [
                                            '$name_parts', 1, {
                                                '$size': '$name_parts'
                                            }
                                        ]
                                    }, 
                                    'initialValue': '', 
                                    'in': {
                                        '$cond': [
                                            {
                                                '$eq': [
                                                    '$$value', ''
                                                ]
                                            }, '$$this', {
                                                '$concat': [
                                                    '$$value', ', ', '$$this'
                                                ]
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    }, 
                    'else': None
                }
            }
        }
    }, {
        '$project': {
            'name_parts': 0
        }
    }, {
        '$out': {
            'db': 'Colecciones_Finales', 
            'coll': 'FooDB_Alimento_Constituyentes'
        }
    }
])