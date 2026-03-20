from pymongo import MongoClient

from pymongo import MongoClient

client = MongoClient("mongodb+srv://krishnanunnir503_db_user:4kwX28sdKlTgO15z@cluster0.3mxzzer.mongodb.net/")
db = client["medsync"]

db.patients.insert_many([
    {"_id": "p1", "name": "John Doe", "clinic": "Clinic X"},
    {"_id": "p2", "name": "Jane Smith", "clinic": "Clinic X"}
])

print("Seed data inserted!")