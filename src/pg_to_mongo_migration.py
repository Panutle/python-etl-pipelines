import os
import psycopg2
from pymongo import MongoClient, InsertOne
from datetime import datetime
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env
load_dotenv()

# Connect Postgresql
HOST_PG = os.getenv('PG_HOST')
PORT_PG = os.getenv('PG_PORT')
DATABASE_PG = os.getenv('PG_DATABASE')
USER_PG = os.getenv('PG_USER')
PASSWORD_PG = os.getenv('PG_PASSWORD')

# Connect MongoDB
USER_MG = os.getenv('MONGO_USER')
PASSWORD_MG = os.getenv('MONGO_PASSWORD')
IP_MG = os.getenv('MONGO_HOST')
PORT_MG = os.getenv('MONGO_PORT')
replcasetname = os.getenv('MONGO_REPLICASET', '') # ถ้าไม่มีค่าใน .env ให้ใช้ string ว่าง

mongo_db = os.getenv('MONGO_DB')
mongo_collection = os.getenv('MONGO_COLLECTION')

def que_data():
    connection = psycopg2.connect(
                host = HOST_PG,
                port = PORT_PG,
                database = DATABASE_PG,
                user = USER_PG,
                password = PASSWORD_PG
    )
    cursor = connection.cursor()

    query = """
        SELECT *
        FROM source_table_name; -- ระบุชื่อ Table ตรงนี้
        """

    cursor.execute(query)
    pg_data = cursor.fetchall()
    print(datetime.now(), " Data len :", len(pg_data))
    cursor.close()
    connection.close()

    return pg_data

def conn_mongo():
    if replcasetname.strip() == '':
        mongo_host = f"mongodb://{USER_MG}:{PASSWORD_MG}@{IP_MG}:{PORT_MG}/"
    else:
        mongo_host = f"mongodb://{USER_MG}:{PASSWORD_MG}@{IP_MG}:{PORT_MG}/{mongo_db}?replicaSet={replcasetname}"

    client = MongoClient(mongo_host)
    db = client[mongo_db]
    collection = db[mongo_collection]

    return db, collection, mongo_collection

def up_to_mongo(data, collection, db):
    print('#### DROP COLLECTION AT MONGO ####')
    collection.drop()

    print(f'#### CREATE COLLECTION AT MONGO {mongo_collection} ####')
    db.create_collection(mongo_collection)

    print('#### START BULK WRITE TO MONGO ####')
    bulk_updates = []

    i = 0

    for row in data:
        user_id = str(row[0])
        ranking = row[1]
        sku_code = row[2]
        create_info_timestamp = row[3].strftime("%Y-%m-%d %H:%M:%S")

        document = {
            'user_id': user_id,
            'ranking': ranking,
            'sku_code': sku_code,
            'create_info_timestamp':create_info_timestamp
        }

        bulk_updates.append(InsertOne(document))

        i += 1

        #ส่งทุกๆ 1000 แถว
        if i % 1000 == 0:
            collection.bulk_write(bulk_updates)
            bulk_updates = []
        elif i == len(data):
            collection.bulk_write(bulk_updates)
            bulk_updates = []

def Check(data, collection):
    total_documents_after_insert = collection.count_documents({})

    if total_documents_after_insert == len(data):
        print(f"Number of documents in {mongo_collection} collection equal fetch data = {total_documents_after_insert}.")
    else:
        print(f"ERROR: Number of documents in {mongo_collection} collection does not equal fetch data {total_documents_after_insert} !=  {len(data)}.")

if __name__ == "__main__":
    starttime = datetime.now()
    print(f'Start Connect Postgresql: {starttime}')

    data = que_data()

    con_mg = datetime.now()
    print(f'Start Connect MongoDB: {con_mg}')
    db, collection, mongo_collection = conn_mongo()

    up_to_mongo(data, collection, db)

    endtime = datetime.now()
    duration = endtime - starttime
    print(f'End Time: {endtime}')
    print(f'Duration: {duration}')

    Check(data, collection)