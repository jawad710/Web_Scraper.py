import os
import json
import pymongo

# MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["almayadeen"]

# Base directory where all your JSON files are stored
base_directory = r"C:\Users\user\PycharmProjects\bootcamp-project\data"

# Loop through all directories (each representing a month and year)
for dir_name in os.listdir(base_directory):
    dir_path = os.path.join(base_directory, dir_name)

    if os.path.isdir(dir_path):  # Ensure it's a directory
        # Extract the year and month from the directory name
        year, month = dir_name.split('_')

        # Loop through all JSON files in the directory
        for filename in os.listdir(dir_path):
            if filename.endswith(".json"):
                file_path = os.path.join(dir_path, filename)

                # Read the JSON file
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # Ensure data is a list of documents (array of JSON objects)
                    if isinstance(data, dict):  # If it's a single document, convert it to a list
                        data = [data]

                    # Add metadata (year and month) to each document
                    for document in data:
                        document["year"] = year
                        document["month"] = month

                    # Insert data into MongoDB
                    collection = db["articles"]
                    collection.insert_many(data)

                print(f"Inserted data from {file_path} into MongoDB.")

print("All data inserted successfully!")