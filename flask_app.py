from flask import Flask, jsonify
from pymongo import MongoClient, UpdateOne
from datetime import datetime, timedelta

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
            iso_date = datetime.strptime(article['publication_date'], "%Y-%m-%dT%H:%M:%S%z")
            bulk_operations.append(
                UpdateOne({"_id": article["_id"]}, {"$set": {"publication_date": iso_date}})
            )
        except Exception as e:
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

# Route for getting articles by title length
@app.route('/articles_by_title_length', methods=['GET'])
def articles_by_title_length():
    pipeline = [
        {"$project": {"title_length": {"$size": {"$split": ["$title", " "]}}}},
        {"$group": {"_id": "$title_length", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# Route for getting articles grouped by coverage
@app.route('/articles_grouped_by_coverage', methods=['GET'])
def articles_grouped_by_coverage():
    pipeline = [
        {"$unwind": "$classes"},
        {"$group": {"_id": "$classes.value", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)


# Route for getting articles by language
@app.route('/articles_by_language', methods=['GET'])
def articles_by_language():
    pipeline = [
        {"$group": {"_id": "$lang", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# Route for getting articles by classes
@app.route('/articles_by_classes', methods=['GET'])
def articles_by_classes():
    pipeline = [
        {"$unwind": "$classes"},
        {"$group": {"_id": "$classes.value", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# Route for getting recent articles
@app.route('/recent_articles', methods=['GET'])
def recent_articles():
    pipeline = [
        {"$sort": {"publication_date": -1}},
        {"$limit": 10}
    ]
    result = list(collection.find({}, {"title": 1, "publication_date": 1, "_id": 0}).sort("publication_date", -1).limit(10))
    return jsonify(result)

# Route for getting articles grouped by keyword
@app.route('/articles_by_keyword/<keyword>', methods=['GET'])
def articles_by_keyword(keyword):
    result = list(collection.find({"keywords": keyword}, {"title": 1, "url": 1, "_id": 0}))
    return jsonify(result)

# Route for getting articles grouped by auther name
@app.route('/articles_by_author/<author_name>', methods=['GET'])
def articles_by_author(author_name):
    result = list(collection.find({"author": author_name}, {"title": 1, "url": 1, "_id": 0}))
    return jsonify(result)

# Route for getting top classes
@app.route('/top_classes', methods=['GET'])
def top_classes():
    pipeline = [
        {"$unwind": "$classes"},
        {"$group": {"_id": "$classes.value", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# Route for getting details of an articles according to post ID
@app.route('/article_details/<postid>', methods=['GET'])
def article_details(postid):
    result = collection.find_one({"post_id": postid}, {"_id": 0})
    return jsonify(result)

# Route for getting articles with video
@app.route('/articles_with_video', methods=['GET'])
def articles_with_video():
    result = list(collection.find({"video_duration": {"$ne": None}}, {"title": 1, "url": 1, "_id": 0}))
    return jsonify(result)

# Route for getting articles by years
@app.route('/articles_by_year/<year>', methods=['GET'])
def articles_by_year(year):
    result = list(collection.find({"year": year}, {"title": 1, "url": 1, "_id": 0}))
    return jsonify(result)

# Route for getting longest article
@app.route('/longest_articles', methods=['GET'])
def longest_articles():
    pipeline = [
        {
            "$project": {
                "title": 1,
                "word_count": {"$size": {"$split": ["$content", " "]}}
            }
        },
        {"$sort": {"word_count": -1}},
        {"$limit": 10}
    ]
    result = list(collection.aggregate(pipeline))

    for item in result:
        item["_id"] = str(item.get("_id"))

    return jsonify(result)

# Route for getting shortest article
@app.route('/shortest_articles', methods=['GET'])
def shortest_articles():
    pipeline = [
        {
            "$project": {
                "title": 1,
                "word_count": {"$size": {"$split": ["$content", " "]}}
            }
        },
        {"$sort": {"word_count": 1}},
        {"$limit": 10}
    ]
    result = list(collection.aggregate(pipeline))
    for item in result:
        item["_id"] = str(item.get("_id"))

    return jsonify(result)

# Route for getting article by keyword count
@app.route('/articles_by_keyword_count', methods=['GET'])
def articles_by_keyword_count():
    pipeline = [
        # Ensure `keywords` is an array and count the number of keywords
        {"$addFields": {"keywords_count": "$count"}},
        # Group by the number of keywords and count the occurrences
        {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
        # Sort by the number of keywords count
        {"$sort": {"_id": 1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)



# Route for getting articles with thumbnail
@app.route('/articles_with_thumbnail', methods=['GET'])
def articles_with_thumbnail():
    result = list(collection.find({"thumbnail": {"$ne": None}}, {"title": 1, "url": 1, "_id": 0}))
    return jsonify(result)

# Route for getting articles updated after publication
@app.route('/articles_updated_after_publication', methods=['GET'])
def articles_updated_after_publication():
    pipeline = [
        {"$addFields": {"publication_date": {"$dateFromString": {"dateString": "$publication_date"}},
                        "last_updated_date": {"$dateFromString": {"dateString": "$last_updated_date"}}}},
        {"$match": {"$expr": {"$gt": ["$last_updated_date", "$publication_date"]}}},
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# Route for getting articles by coverage
@app.route('/articles_by_coverage/<coverage>', methods=['GET'])
def articles_by_coverage(coverage):
    result = list(collection.find({"classes.value": coverage}, {"title": 1, "url": 1, "_id": 0}))
    return jsonify(result)

# Route for getting popular keyword last X days
@app.route('/popular_keywords_last_X_days/<int:days>', methods=['GET'])
def popular_keywords_last_X_days(days):
    cutoff_date = datetime.now() - timedelta(days=days)
    pipeline = [
        {"$match": {"publication_date": {"$gte": cutoff_date.isoformat()}}},
        {"$unwind": "$keywords"},
        {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# Route for getting articles by month
@app.route('/articles_by_month/<year>/<month>', methods=['GET'])
def articles_by_month(year, month):
    result = list(collection.find({"year": year, "month": month}, {"title": 1, "url": 1, "_id": 0}))
    return jsonify(result)

# Route for getting articles by word count range
@app.route('/articles_by_word_count_range/<int:min>/<int:max>', methods=['GET'])
def articles_by_word_count_range(min, max):
    pipeline = [
        {"$project": {"word_count": {"$size": {"$split": ["$content", " "]}}}},
        {"$match": {"word_count": {"$gte": min, "$lte": max}}},
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# Route for getting articles by specific date
@app.route('/articles_by_specific_date/<date>', methods=['GET'])
def articles_by_specific_date(date):
    result = list(collection.find({"publication_date": date}, {"title": 1, "url": 1, "_id": 0}))
    return jsonify(result)

# Route for getting articles containing text
@app.route('/articles_containing_text/<text>', methods=['GET'])
def articles_containing_text(text):
    result = list(collection.find({"content": {"$regex": text}}, {"title": 1, "url": 1, "_id": 0}))
    return jsonify(result)

# Route for getting articles with more than N words
@app.route('/articles_with_more_than/<int:word_count>', methods=['GET'])
def articles_with_more_than(word_count):
    pipeline = [
        {"$project": {"title": 1, "url": 1, "word_count": {"$size": {"$split": ["$content", " "]}}}},
        {"$match": {"word_count": {"$gt": word_count}}},
        {"$sort": {"word_count": -1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
