from flask import Flask, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient, UpdateOne
from datetime import datetime, timedelta
from bson import ObjectId


app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["almayadeen"]
collection = db["articles"]

CORS(app, origins=["http://localhost:63342"])

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
@app.route('/articles_by_publication_date', methods=['GET'])
def articles_by_publication_date():
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

# Route for getting articles grouped by auther name with author's name
@app.route('/articles_by_author/<author_name>', methods=['GET'])
def articles_by_author(author_name):
    result = list(collection.find({"author": author_name}, {"title": 1, "url": 1, "_id": 0}))
    return jsonify(result)

# Route for getting articles grouped by auther name
@app.route('/articles_by_authors', methods=['GET'])
def articles_by_authors():
    pipeline = [
        {"$group": {"_id": "$author", "article_count": {"$sum": 1}}}
    ]
    result = list(collection.aggregate(pipeline))
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

# Route for getting details of all articles
@app.route('/article_details', methods=['GET'])
def all_article_details():
    result = list(collection.find({}, {"_id": 0, "title": 1, "keywords": 1, "publication_date": 1}))
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
@app.route('/articles_by_thumbnail', methods=['GET'])
def articles_by_thumbnail():
    pipeline = [
        # Group articles based on whether they have a thumbnail or not
        {
            "$group": {
                "_id": {
                    "$cond": {
                        "if": {"$ne": ["$thumbnail", None]},  # If thumbnail is not None
                        "then": "with_thumbnail",
                        "else": "without_thumbnail"
                    }
                },
                "count": {"$sum": 1}  # Count the number of articles in each group
            }
        }
    ]

    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# Route for getting articles updated after publication
@app.route('/articles_updated_after_publication', methods=['GET'])
def articles_updated_after_publication():
    pipeline = [
        {
            "$match": {
                "$expr": {
                    "$gt": [
                        {"$toDate": "$last_updated_date"},
                        {"$toDate": "$publication_date"}
                    ]
                }
            }
        }
    ]
    result = list(collection.aggregate(pipeline))

    # Convert ObjectId to string for JSON serialization
    for doc in result:
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])

    return jsonify(result)


# Route for getting articles by coverage
@app.route('/articles_by_coverage', methods=['GET'])
def articles_by_coverage():
    pipeline = [
        # Unwind the 'classes' array to access each 'value' inside
        {"$unwind": "$classes"},
        # Group by the 'classes.value' field and count the number of articles for each coverage
        {"$group": {"_id": "$classes.value", "count": {"$sum": 1}}},
        # Sort by coverage (optional)
        {"$sort": {"_id": 1}}
    ]

    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# Route for getting popular keywords last X days
@app.route('/popular_keywords_last_X_days/<int:days>', methods=['GET'])
def popular_keywords_last_X_days(days):
    cutoff_date = datetime.now() - timedelta(days=days)
    pipeline = [
        {"$match": {"publication_date": {"$gte": cutoff_date}}},
        {"$unwind": "$keywords"},
        {
            "$group": {
                "_id": {
                    "keyword": "$keywords",
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$publication_date"}}
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]

    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# Route for getting articles by months
@app.route('/articles_by_month', methods=['GET'])
def articles_by_month():
    pipeline = [
        {
            "$addFields": {
                "date_field": {
                    "$dateFromString": {
                        "dateString": "$date_field"  # Replace 'date_field' with your actual date field
                    }
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$date_field"},
                    "month": {"$month": "$date_field"}
                },
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "date": {
                    "$dateFromParts": {
                        "year": "$_id.year",
                        "month": "$_id.month",
                        "day": 1
                    }
                },
                "count": 1
            }
        },
        {
            "$sort": {
                "date": 1
            }
        }
    ]

    result = list(collection.aggregate(pipeline))
    return jsonify(result)


# Route for getting articles by word count range
@app.route('/articles_by_word_count_range', methods=['GET'])
def articles_by_word_count_range():
    pipeline = [
        {
            "$project": {
                "word_count": {"$size": {"$split": ["$content", " "]}}
            }
        },
        {
            "$bucket": {
                "groupBy": "$word_count",
                "boundaries": [0, 100, 500, 1000, 5000, 10000],  #these are the ranges of the articles
                "default": "Over 10,000",  # Anything over 10,000 words goes into this bucket
                "output": {
                    "count": {"$sum": 1}  #the number of articles in each range
                }
            }
        }
    ]

    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# Route for getting articles by specific date
@app.route('/articles_by_specific_date/<date>', methods=['GET'])
def articles_by_specific_date(date):
    result = list(collection.find({"publication_date": date}, {"title": 1, "url": 1, "_id": 0}))
    return jsonify(result)


# Route to get articles grouped by specific dates
@app.route('/articles_by_specific_date', methods=['GET'])
def articles_by_specific_date():
    pipeline = [
        # Convert publication_date from string to date if necessary and extract the date part
        {"$addFields": {
            "parsed_date": {
                "$dateFromString": {
                    "dateString": "$publication_date",
                    "format": "%Y-%m-%dT%H:%M:%S.%L%z"
                }
            }
        }},
        # Group articles by the date part only (year, month, day)
        {"$group": {
            "_id": {
                "$dateToString": {
                    "format": "%Y-%m-%d",
                    "date": "$parsed_date"
                }
            },
            "count": {"$sum": 1}
        }},
        # Sort by date in ascending order
        {"$sort": {"_id": 1}}
    ]

    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# Route for getting articles with a specific number of keywords
@app.route('/articles_with_keyword_count/<int:keyword_count>', methods=['GET'])
def articles_with_keyword_count(keyword_count):
    pipeline = [
        # Add a field for the length of the 'keywords' array
        {"$addFields": {"keyword_count": {"$size": "$keywords"}}},
        # Match documents where the keyword count is equal to the specified count
        {"$match": {"keyword_count": keyword_count}},
        # Project the desired fields
        {"$project": {"title": 1, "url": 1, "keyword_count": 1, "_id": 0}}
    ]

    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# Route for getting articles containing text
@app.route('/articles_containing_text/<text>', methods=['GET'])
def articles_containing_text(text):
    result = list(collection.find({"content": {"$regex": text}}, {"title": 1, "url": 1, "_id": 0}))
    return jsonify(result)


# Route for getting articles with specific keyword
@app.route('/articles_with_keyword/<keyword>', methods=['GET'])
def articles_with_keyword(keyword):
    pipeline = [
        {
            "$match": {
                "keywords": {"$regex": keyword, "$options": "i"}  # Case-insensitive search for keyword
            }
        },
        {
            "$group": {
                "_id": None,  # We don't need to group by a specific field, just count
                "keyword": {"$first": keyword},  # Include the keyword itself in the result
                "count": {"$sum": 1}  # Count the matching articles
            }
        },
        {
            "$project": {
                "_id": 0,  # Exclude the _id field from the result
                "keyword": 1,
                "count": 1
            }
        }
    ]

    result = list(collection.aggregate(pipeline))

    return jsonify(result[0] if result else {"keyword": keyword, "count": 0})

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
