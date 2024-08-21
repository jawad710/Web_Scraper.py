from flask import Flask, jsonify
from pymongo import MongoClient, UpdateOne
from datetime import datetime

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["almayadeen"]
collection = db["articles"]

# Helper function to convert string dates to ISODate
def convert_string_dates_to_iso():
    bulk_operations = []
    articles = collection.find({"publication_date": {"$type": "string"}})

    for article in articles:
        try:
            # Convert the string date to a datetime object
            iso_date = datetime.strptime(article['publication_date'], "%Y-%m-%dT%H:%M:%S%z")
            # Prepare the bulk update operation
            bulk_operations.append(
                UpdateOne({"_id": article["_id"]}, {"$set": {"publication_date": iso_date}})
            )
        except Exception as e:
            # Handle any exceptions that occur during conversion
            print(f"Error converting date for article {article['_id']}: {e}")

    # Execute the bulk operations if there are any
    if bulk_operations:
        collection.bulk_write(bulk_operations)

# Route for getting top keywords
@app.route('/top_keywords', methods=['GET'])
def top_keywords():
    pipeline = [
        {"$unwind": "$keywords"},
        {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# Route for getting top authors
@app.route('/top_authors', methods=['GET'])
def top_authors():
    pipeline = [
        {"$group": {"_id": "$author", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# Route for getting articles by publication date
@app.route('/articles_by_date', methods=['GET'])
def articles_by_date():
    # Convert string dates to ISODate before running the aggregation pipeline
    convert_string_dates_to_iso()

    pipeline = [
        {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$publication_date"}}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# Route for getting articles by word count
@app.route('/articles_by_word_count', methods=['GET'])
def articles_by_word_count():
    pipeline = [
        {"$project": {"word_count": {"$size": {"$split": ["$content", " "]}}}},
        {"$group": {"_id": "$word_count", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
