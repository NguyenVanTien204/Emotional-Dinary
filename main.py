from flask import Flask, request, jsonify, render_template
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from bson.json_util import dumps
import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

# MongoDB configuration - adjust URI as needed
app.config["MONGO_URI"] = "mongodb://localhost:27017/emotional_diary_db"
mongo = PyMongo(app)
entries_collection = mongo.db.entries


def entry_to_json(entry):
    
    return {
        "_id": str(entry["_id"]),
        "date": entry["date"],
        "content": entry["content"],
        "emotions": entry["emotions"]
    }

@app.route("/entries", methods=["POST"])
def create_entry():
    data = request.get_json()
    if not data or "date" not in data or "content" not in data:
        return jsonify({"error": "Missing required fields: date, content"}), 400

    date = data["date"]
    # Validate date format
    try:
        datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Date must be in YYYY-MM-DD format"}), 400

    content = data["content"]
    emotions = data.get("emotions", [])
    if not isinstance(emotions, list):
        return jsonify({"error": "Emotions must be a list of strings"}), 400

    entry = {
        "date": date,
        "content": content,
        "emotions": emotions
    }
    result = entries_collection.insert_one(entry)
    new_entry = entries_collection.find_one({"_id": result.inserted_id})
    return jsonify(entry_to_json(new_entry)), 201
@app.route("/")
def home():
    return jsonify({"message": "Welcome to the Emotional Diary API"}), 200

if __name__ == "__main__":
    app.run(debug=True)
