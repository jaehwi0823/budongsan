from pymongo import MongoClient
# from pymongo.cursor import CursorType


###############################################################################
#  Insert
###############################################################################
def insert_item_one(db_name, collection_name, data):
    with MongoClient('localhost', 27017) as mongo:
        result = mongo[db_name][collection_name].insert_one(data)
    return result.inserted_id

def insert_item_many(db_name, collection_name, datas):
    with MongoClient('localhost', 27017) as mongo:
        result = mongo[db_name][collection_name].insert_many(datas)
    return result.inserted_ids


###############################################################################
#  Select
###############################################################################
def find_item_one(db_name, collection_name, condition=None):
    with MongoClient('localhost', 27017) as mongo:
        result = mongo[db_name][collection_name].find_one(condition, {"_id": False})
    return result

def find_item(db_name, collection_name, condition=None, fields=None):
    with MongoClient('localhost', 27017) as mongo:
        if fields:
            myFields = {"_id": False}
            myFields.update(fields)
        else:
            myFields = {"_id": False}
        result = mongo[db_name][collection_name].find(condition, myFields)
    return result


###############################################################################
#  drop
###############################################################################
def delete_item_one(db_name, collection_name, condition=None):
    with MongoClient('localhost', 27017) as mongo:
        result = mongo[db_name][collection_name].delete_one(condition)
    return result
def delete_item(db_name, collection_name, condition=None):
    with MongoClient('localhost', 27017) as mongo:
        result = mongo[db_name][collection_name].delete_many(condition)
    return result